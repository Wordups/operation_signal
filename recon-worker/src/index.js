// Operation SIGNAL — Recon Worker (Cloudflare Worker)
// Blueprint §4.1: cron 07:00 ET → last 30 uploads per watchlist channel →
// VPH outlier detector → formula extractor → gap detector → Discord digest.
// YouTube Data API v3 only. ~10 quota units/day at 4 channels (limit: 10,000).

const API = "https://www.googleapis.com/youtube/v3";
const OUTLIER_MULTIPLIER = 3;
const UPLOADS_PER_CHANNEL = 30;

// KV key "watchlist" (JSON array of @handles / UC ids) overrides this.
const DEFAULT_WATCHLIST = ["@airevolutionx", "@TheAiGrid", "@theAIsearch", "@intheworldofai"];

// Buyer-intent markers. Low coverage across all target uploads = open lane.
const BUYER_INTENT = [
  "worth it", "should you buy", "review", " vs ", "price", "under $", "cost",
  "before you buy", "honest", "don't buy", "dont buy", "ranked", "wait",
  "per month", "monthly", "buying", "buyer", "actually buy", "scam",
];

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runRecon(env));
  },

  // Manual trigger: GET /run with header  x-run-token: <RUN_TOKEN>
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== "/run") return new Response("signal-recon: alive", { status: 200 });
    if (request.headers.get("x-run-token") !== env.RUN_TOKEN) {
      return new Response("forbidden", { status: 403 });
    }
    const digest = await runRecon(env);
    return new Response(digest, { status: 200, headers: { "content-type": "text/plain; charset=utf-8" } });
  },
};

async function runRecon(env) {
  const watchlist = JSON.parse((await env.SIGNAL_KV.get("watchlist")) ?? "null") ?? DEFAULT_WATCHLIST;
  const channels = [];
  const errors = [];

  for (const target of watchlist) {
    try {
      channels.push(await reconChannel(target, env));
    } catch (err) {
      errors.push(`${target}: ${err.message}`);
    }
  }

  const digest = buildDigest(channels, errors);
  if (env.DISCORD_WEBHOOK_URL) await postDiscord(env.DISCORD_WEBHOOK_URL, digest);
  return digest.text;
}

// ---------- per-channel recon ----------

async function reconChannel(target, env) {
  const channel = await resolveChannel(target, env);
  const videos = await fetchRecentUploads(channel, env);

  const med = median(videos.map((v) => v.views));
  const now = Date.now();
  for (const v of videos) {
    v.hoursLive = Math.max(1, (now - Date.parse(v.publishedAt)) / 3_600_000);
    v.vph = v.views / v.hoursLive;
    v.outlierScore = med ? v.views / med : 0;
  }
  const outliers = videos
    .filter((v) => v.outlierScore >= OUTLIER_MULTIPLIER)
    .sort((a, b) => b.outlierScore - a.outlierScore);

  // New since last run
  const seenKey = `seen:${channel.id}`;
  const seen = new Set(JSON.parse((await env.SIGNAL_KV.get(seenKey)) ?? "[]"));
  const fresh = videos.filter((v) => !seen.has(v.id));
  await env.SIGNAL_KV.put(seenKey, JSON.stringify(videos.map((v) => v.id)));

  return { channel, videos, medianViews: med, outliers, fresh };
}

async function resolveChannel(target, env) {
  const cacheKey = `channel:${target}`;
  const cached = await env.SIGNAL_KV.get(cacheKey, "json");
  if (cached) return cached;

  const isId = /^UC[\w-]{22}$/.test(target);
  const res = await yt("channels", {
    part: "snippet,contentDetails",
    ...(isId ? { id: target } : { forHandle: target.startsWith("@") ? target : "@" + target }),
  }, env);
  if (!res.items?.length) throw new Error("channel not found");
  const c = res.items[0];
  const channel = {
    id: c.id,
    title: c.snippet.title,
    uploadsPlaylist: c.contentDetails.relatedPlaylists.uploads,
  };
  await env.SIGNAL_KV.put(cacheKey, JSON.stringify(channel), { expirationTtl: 30 * 86400 });
  return channel;
}

async function fetchRecentUploads(channel, env) {
  const list = await yt("playlistItems", {
    part: "contentDetails",
    playlistId: channel.uploadsPlaylist,
    maxResults: String(UPLOADS_PER_CHANNEL),
  }, env);
  const ids = (list.items ?? []).map((i) => i.contentDetails.videoId);
  if (!ids.length) return [];

  const res = await yt("videos", {
    part: "snippet,statistics,contentDetails",
    id: ids.join(","),
  }, env);
  return (res.items ?? [])
    .filter((v) => v.snippet.liveBroadcastContent === "none")
    .map((v) => ({
      id: v.id,
      title: v.snippet.title,
      publishedAt: v.snippet.publishedAt,
      durationSec: isoDurationToSeconds(v.contentDetails.duration),
      views: Number(v.statistics.viewCount ?? 0),
    }));
}

async function yt(endpoint, params, env) {
  const url = new URL(`${API}/${endpoint}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  url.searchParams.set("key", env.YT_API_KEY);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${endpoint} ${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}

// ---------- analysis ----------

function isoDurationToSeconds(iso) {
  const m = iso?.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!m) return 0;
  return Number(m[1] ?? 0) * 3600 + Number(m[2] ?? 0) * 60 + Number(m[3] ?? 0);
}

function median(nums) {
  if (!nums.length) return 0;
  const s = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

const STOPWORDS = new Set(("a an and are as at be but by for from has have how i if in is it its of on or " +
  "that the this to was we what when why will with you your not just so").split(" "));

function extractFormulas(titles) {
  const counts = new Map();
  for (const title of titles) {
    const toks = title.toLowerCase().replace(/[^\p{L}\p{N}\s'$]/gu, " ").split(/\s+/).filter(Boolean);
    for (const n of [2, 3]) {
      for (let i = 0; i <= toks.length - n; i++) {
        const gram = toks.slice(i, i + n);
        if (gram.every((t) => STOPWORDS.has(t))) continue;
        const key = gram.join(" ");
        counts.set(key, (counts.get(key) ?? 0) + 1);
      }
    }
  }
  return [...counts.entries()].filter(([, c]) => c >= 2).sort((a, b) => b[1] - a[1]).slice(0, 8);
}

function gapReport(allTitles) {
  const lower = allTitles.map((t) => " " + t.toLowerCase() + " ");
  return BUYER_INTENT.map((kw) => ({
    kw: kw.trim(),
    hits: lower.filter((t) => t.includes(kw.toLowerCase())).length,
  })).sort((a, b) => a.hits - b.hits);
}

// ---------- digest ----------

const fmt = (n) => Math.round(n).toLocaleString("en-US");

function buildDigest(channels, errors) {
  const allVideos = channels.flatMap((c) => c.videos);
  const allOutliers = channels.flatMap((c) => c.outliers.map((v) => ({ ...v, channel: c.channel.title })))
    .sort((a, b) => b.outlierScore - a.outlierScore);
  const freshCount = channels.reduce((a, c) => a + c.fresh.length, 0);
  const formulas = extractFormulas(allOutliers.map((v) => v.title));
  const gaps = gapReport(allVideos.map((v) => v.title));
  const open = gaps.filter((g) => g.hits === 0).map((g) => g.kw);
  const covered = gaps.filter((g) => g.hits > 0);

  const lines = [];
  lines.push(`**SIGNAL Recon — ${channels.length} channels, ${allVideos.length} uploads scanned, ${freshCount} new since last run**`);

  lines.push("", `**Outliers (≥${OUTLIER_MULTIPLIER}× channel median):**`);
  if (allOutliers.length) {
    for (const v of allOutliers.slice(0, 6)) {
      lines.push(`• ${v.outlierScore.toFixed(1)}× · ${fmt(v.vph)} VPH · ${Math.round(v.durationSec / 60)}m — [${v.title}](https://youtu.be/${v.id}) (${v.channel})`);
    }
  } else lines.push("• none today");

  lines.push("", "**Recurring formulas in outlier titles:**");
  if (formulas.length) for (const [g, c] of formulas) lines.push(`• "${g}" ×${c}`);
  else lines.push("• not enough outliers to mine");

  lines.push("", "**Gap detector — buyer-intent terms NOBODY on the watchlist is using:**");
  lines.push(open.length ? "• " + open.join(" · ") : "• all buyer terms have some coverage today");
  if (covered.length) {
    lines.push("**Thin coverage (≤2 hits):**");
    lines.push("• " + covered.filter((g) => g.hits <= 2).map((g) => `${g.kw} (${g.hits})`).join(" · "));
  }

  lines.push("", "**Channel medians (last 30):**");
  for (const c of channels) {
    lines.push(`• ${c.channel.title}: median ${fmt(c.medianViews)} views · ${c.outliers.length} outliers · ${c.fresh.length} new`);
  }

  if (errors.length) lines.push("", "**Errors:** " + errors.join(" | "));

  return { text: lines.join("\n") };
}

async function postDiscord(webhookUrl, digest) {
  // Discord embed description cap is 4096.
  const body = {
    embeds: [{
      title: "📡 Operation SIGNAL — Daily Recon",
      description: digest.text.slice(0, 4000),
      color: 0x5865f2,
      timestamp: new Date().toISOString(),
    }],
  };
  const res = await fetch(webhookUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Discord webhook ${res.status}: ${(await res.text()).slice(0, 200)}`);
}
