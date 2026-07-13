#!/usr/bin/env node
// Operation SIGNAL — Recon Worker
// Pulls emulation-target channels via YouTube Data API v3, finds outliers,
// extracts title patterns, and writes report.md + titles.csv + raw JSON.
// Zero dependencies. Node 18+.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(ROOT, "data");
const API = "https://www.googleapis.com/youtube/v3";

// ---------- config ----------

function loadConfig() {
  const cfgPath = path.join(ROOT, "config.json");
  if (!fs.existsSync(cfgPath)) {
    console.error("No config.json found. Copy config.example.json to config.json, add your API key and targets.");
    process.exit(1);
  }
  const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
  cfg.apiKey = cfg.apiKey || process.env.YT_API_KEY;
  if (!cfg.apiKey || cfg.apiKey.startsWith("PASTE_")) {
    console.error("No API key. Set apiKey in config.json or the YT_API_KEY env var.");
    process.exit(1);
  }
  if (!Array.isArray(cfg.targets) || cfg.targets.length === 0) {
    console.error("No targets in config.json. Add channel handles (@name), channel IDs (UC...), or channel URLs.");
    process.exit(1);
  }
  cfg.maxVideos = cfg.maxVideos ?? 200;
  cfg.outlierMultiplier = cfg.outlierMultiplier ?? 3;
  cfg.shortFormMaxSeconds = cfg.shortFormMaxSeconds ?? 180;
  return cfg;
}

// ---------- api ----------

let quotaUnits = 0;

async function yt(endpoint, params, apiKey) {
  const url = new URL(`${API}/${endpoint}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  url.searchParams.set("key", apiKey);
  quotaUnits += 1;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${endpoint} ${res.status}: ${body.slice(0, 300)}`);
  }
  return res.json();
}

function parseTarget(raw) {
  const t = raw.trim();
  let m;
  if ((m = t.match(/youtube\.com\/channel\/(UC[\w-]{22})/))) return { channelId: m[1] };
  if ((m = t.match(/youtube\.com\/(@[\w.-]+)/))) return { handle: m[1] };
  if (/^UC[\w-]{22}$/.test(t)) return { channelId: t };
  return { handle: t.startsWith("@") ? t : "@" + t };
}

async function resolveChannel(target, apiKey) {
  const parsed = parseTarget(target);
  const params = {
    part: "snippet,statistics,contentDetails",
    ...(parsed.channelId ? { id: parsed.channelId } : { forHandle: parsed.handle }),
  };
  const res = await yt("channels", params, apiKey);
  if (!res.items?.length) throw new Error(`Channel not found: ${target}`);
  const c = res.items[0];
  return {
    id: c.id,
    title: c.snippet.title,
    handle: c.snippet.customUrl || parsed.handle || "",
    subs: Number(c.statistics.subscriberCount ?? 0),
    totalVideos: Number(c.statistics.videoCount ?? 0),
    totalViews: Number(c.statistics.viewCount ?? 0),
    uploadsPlaylist: c.contentDetails.relatedPlaylists.uploads,
  };
}

async function fetchUploads(channel, maxVideos, apiKey) {
  const videoIds = [];
  let pageToken = "";
  while (videoIds.length < maxVideos) {
    const res = await yt("playlistItems", {
      part: "contentDetails",
      playlistId: channel.uploadsPlaylist,
      maxResults: "50",
      ...(pageToken ? { pageToken } : {}),
    }, apiKey);
    for (const item of res.items ?? []) videoIds.push(item.contentDetails.videoId);
    pageToken = res.nextPageToken;
    if (!pageToken) break;
  }
  const videos = [];
  for (let i = 0; i < Math.min(videoIds.length, maxVideos); i += 50) {
    const batch = videoIds.slice(i, i + 50);
    const res = await yt("videos", {
      part: "snippet,statistics,contentDetails",
      id: batch.join(","),
      maxResults: "50",
    }, apiKey);
    for (const v of res.items ?? []) {
      if (v.snippet.liveBroadcastContent !== "none") continue; // skip live/upcoming
      videos.push({
        id: v.id,
        title: v.snippet.title,
        publishedAt: v.snippet.publishedAt,
        durationSec: isoDurationToSeconds(v.contentDetails.duration),
        views: Number(v.statistics.viewCount ?? 0),
        likes: Number(v.statistics.likeCount ?? 0),
        comments: Number(v.statistics.commentCount ?? 0),
      });
    }
  }
  return videos;
}

function isoDurationToSeconds(iso) {
  const m = iso?.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!m) return 0;
  return (Number(m[1] ?? 0) * 3600) + (Number(m[2] ?? 0) * 60) + Number(m[3] ?? 0);
}

// ---------- analysis ----------

function median(nums) {
  if (!nums.length) return 0;
  const s = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

const STOPWORDS = new Set(("a an and are as at be but by for from has have how i if in is it its of on or " +
  "that the this to was we what when why will with you your not just so do does did can could should would " +
  "my me our us they them their there here about into over under after before more most").split(" "));

function tokens(title) {
  return title.toLowerCase().replace(/[^\p{L}\p{N}\s']/gu, " ").split(/\s+/).filter(Boolean);
}

function ngrams(titles, n) {
  const counts = new Map();
  for (const title of titles) {
    const toks = tokens(title);
    for (let i = 0; i <= toks.length - n; i++) {
      const gram = toks.slice(i, i + n);
      if (gram.every((t) => STOPWORDS.has(t))) continue;
      const key = gram.join(" ");
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }
  return [...counts.entries()].filter(([, c]) => c >= 2).sort((a, b) => b[1] - a[1]);
}

const FORMAT_FLAGS = {
  "starts with number": (t) => /^\d/.test(t.trim()),
  "contains a number": (t) => /\d/.test(t),
  "how/why/what lead": (t) => /^(how|why|what)\b/i.test(t.trim()),
  "question mark": (t) => t.includes("?"),
  "brackets/parens tag": (t) => /[\[\(].+[\]\)]/.test(t),
  "colon split": (t) => t.includes(":"),
  "vs / versus": (t) => /\bvs\.?\b|\bversus\b/i.test(t),
  "ALL-CAPS word": (t) => /\b[A-Z]{3,}\b/.test(t),
  "year mention": (t) => /\b20\d{2}\b/.test(t),
  "negative hook (stop/never/worst/mistake)": (t) => /\b(stop|never|worst|mistake|avoid|wrong|don'?t)\b/i.test(t),
  "money figure ($, K, million)": (t) => /\$[\d,.]+|[\d.]+\s?(k|million|billion)\b/i.test(t),
  "you/your address": (t) => /\byou\b|\byour\b/i.test(t),
};

function analyzeChannel(channel, videos, cfg) {
  const longForm = videos.filter((v) => v.durationSec > cfg.shortFormMaxSeconds);
  const shortForm = videos.filter((v) => v.durationSec <= cfg.shortFormMaxSeconds);
  const med = median(longForm.map((v) => v.views));
  const scored = longForm
    .map((v) => ({ ...v, outlierScore: med ? v.views / med : 0 }))
    .sort((a, b) => b.outlierScore - a.outlierScore);
  const outliers = scored.filter((v) => v.outlierScore >= cfg.outlierMultiplier);

  const now = Date.now();
  const last90 = longForm.filter((v) => now - Date.parse(v.publishedAt) <= 90 * 86400_000);
  const cadencePerWeek = last90.length / (90 / 7);

  const durations = longForm.map((v) => v.durationSec);
  const bucketViews = {};
  for (const v of longForm) {
    const bucket = v.durationSec < 600 ? "3-10 min" : v.durationSec < 1200 ? "10-20 min" : v.durationSec < 1800 ? "20-30 min" : "30+ min";
    (bucketViews[bucket] ??= []).push(v.views);
  }

  return {
    channel, medianViews: med, cadencePerWeek,
    longFormCount: longForm.length, shortFormCount: shortForm.length,
    avgDurationMin: durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length / 60 : 0,
    viewsByDuration: Object.fromEntries(Object.entries(bucketViews).map(([k, v]) => [k, { count: v.length, medianViews: median(v) }])),
    scored, outliers,
  };
}

function formatLift(allTitles, outlierTitles) {
  const rows = [];
  for (const [name, test] of Object.entries(FORMAT_FLAGS)) {
    const base = allTitles.filter(test).length / (allTitles.length || 1);
    const out = outlierTitles.filter(test).length / (outlierTitles.length || 1);
    if (out === 0 && base === 0) continue;
    rows.push({ name, baseline: base, outlier: out, lift: base ? out / base : (out > 0 ? Infinity : 0) });
  }
  return rows.sort((a, b) => b.lift - a.lift);
}

// ---------- output ----------

const fmt = (n) => Math.round(n).toLocaleString("en-US");
const pct = (n) => (n * 100).toFixed(0) + "%";
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function writeCsv(results) {
  const esc = (s) => `"${String(s).replaceAll('"', '""')}"`;
  const lines = ["channel,title,views,outlier_score,duration_min,published,url"];
  for (const r of results) {
    for (const v of r.scored) {
      lines.push([esc(r.channel.title), esc(v.title), v.views, v.outlierScore.toFixed(2),
        (v.durationSec / 60).toFixed(1), v.publishedAt.slice(0, 10), `https://youtu.be/${v.id}`].join(","));
    }
  }
  fs.writeFileSync(path.join(ROOT, "titles.csv"), lines.join("\n"));
}

function writeReport(results, cfg) {
  const L = [];
  L.push(`# SIGNAL Recon Report`, "");
  L.push(`Targets: ${results.length} · Long-form analyzed: ${results.reduce((a, r) => a + r.longFormCount, 0)} videos · Outlier threshold: ${cfg.outlierMultiplier}x channel median`, "");

  L.push(`## Channel overview`, "");
  L.push(`| Channel | Subs | Median views (long-form) | Cadence /wk (90d) | Avg length | Outliers |`);
  L.push(`|---|---|---|---|---|---|`);
  for (const r of results) {
    L.push(`| ${r.channel.title} | ${fmt(r.channel.subs)} | ${fmt(r.medianViews)} | ${r.cadencePerWeek.toFixed(1)} | ${r.avgDurationMin.toFixed(0)} min | ${r.outliers.length} |`);
  }
  L.push("");

  const allTitles = results.flatMap((r) => r.scored.map((v) => v.title));
  const outlierTitles = results.flatMap((r) => r.outliers.map((v) => v.title));

  L.push(`## Title format lift (outliers vs baseline)`, "");
  L.push(`What appears disproportionately in ${cfg.outlierMultiplier}x+ videos. Lift > 1.5 = validated hook element.`, "");
  L.push(`| Format element | Baseline | In outliers | Lift |`);
  L.push(`|---|---|---|---|`);
  for (const row of formatLift(allTitles, outlierTitles)) {
    L.push(`| ${row.name} | ${pct(row.baseline)} | ${pct(row.outlier)} | ${row.lift === Infinity ? "∞" : row.lift.toFixed(1) + "x"} |`);
  }
  L.push("");

  L.push(`## Recurring phrases in outlier titles`, "");
  const grams = [...ngrams(outlierTitles, 3).slice(0, 10), ...ngrams(outlierTitles, 2).slice(0, 15)];
  if (grams.length) for (const [g, c] of grams) L.push(`- "${g}" ×${c}`);
  else L.push(`_Not enough outliers for phrase mining — lower outlierMultiplier or add targets._`);
  L.push("");

  for (const r of results) {
    L.push(`## ${r.channel.title} (${r.channel.handle}) — ${fmt(r.channel.subs)} subs`, "");
    L.push(`Median ${fmt(r.medianViews)} views · ${r.cadencePerWeek.toFixed(1)} uploads/wk · long-form ${r.longFormCount}, shorts ${r.shortFormCount}`, "");
    L.push(`**Views by video length:**`);
    for (const [bucket, s] of Object.entries(r.viewsByDuration)) {
      L.push(`- ${bucket}: ${s.count} videos, median ${fmt(s.medianViews)} views`);
    }
    L.push("", `**Top outliers:**`, "");
    L.push(`| Score | Views | Length | Title |`);
    L.push(`|---|---|---|---|`);
    for (const v of r.scored.slice(0, 15)) {
      L.push(`| ${v.outlierScore.toFixed(1)}x | ${fmt(v.views)} | ${(v.durationSec / 60).toFixed(0)}m | [${v.title.replaceAll("|", "\\|")}](https://youtu.be/${v.id}) |`);
    }
    L.push("");
  }

  L.push(`---`, `Quota used this run: ~${quotaUnits} units (daily free limit: 10,000).`);
  fs.writeFileSync(path.join(ROOT, "report.md"), L.join("\n"));
}

// ---------- main ----------

const cfg = loadConfig();
fs.mkdirSync(DATA_DIR, { recursive: true });
const results = [];
for (const target of cfg.targets) {
  process.stdout.write(`Recon: ${target} ... `);
  try {
    const channel = await resolveChannel(target, cfg.apiKey);
    const videos = await fetchUploads(channel, cfg.maxVideos, cfg.apiKey);
    const analysis = analyzeChannel(channel, videos, cfg);
    results.push(analysis);
    fs.writeFileSync(path.join(DATA_DIR, `${slug(channel.title)}.json`), JSON.stringify({ channel, videos, medianViews: analysis.medianViews }, null, 2));
    console.log(`${videos.length} videos, median ${fmt(analysis.medianViews)}, ${analysis.outliers.length} outliers`);
  } catch (err) {
    console.log(`FAILED — ${err.message}`);
  }
}
if (!results.length) {
  console.error("No channels resolved. Nothing to report.");
  process.exit(1);
}
writeCsv(results);
writeReport(results, cfg);
console.log(`\nDone. report.md + titles.csv written. Quota used: ~${quotaUnits} units.`);
