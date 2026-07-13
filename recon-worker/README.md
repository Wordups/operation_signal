# Operation SIGNAL — Recon Worker

Blueprint §4.1. Two layers, same brain:

| Layer | File | Job |
|---|---|---|
| **Daily Worker** | `src/index.js` (Cloudflare Worker) | Cron 07:00 ET → last 30 uploads per watchlist channel → VPH outliers → formula extraction → buyer-intent gap detector → Discord digest |
| **Deep Recon CLI** | `recon.js` (local Node) | One-shot deep dive: up to 200 videos/channel → `report.md` (format lift, phrase mining, duration sweet spots) + `titles.csv` + raw JSON. Feeds the Title Formula Library. |

Both use YouTube Data API v3 only — free tier, ToS-clean (C-boundary per blueprint §4.1). Daily worker uses ~10 quota units/day; a full CLI run ~40. Limit is 10,000/day.

## One-time setup: API key

1. [Google Cloud Console](https://console.cloud.google.com/) → new project (e.g. `signal-recon`)
2. APIs & Services → Library → enable **YouTube Data API v3**
3. Credentials → Create credentials → **API key** (restrict it to YouTube Data API v3)

## Deep Recon CLI (run this first — builds the title library)

```powershell
cd G:\dev\operation-signal\recon-worker
copy config.example.json config.json
# paste your API key into config.json (targets are pre-loaded from blueprint §1)
node recon.js
```

Outputs: `report.md`, `titles.csv`, `data/<channel>.json`. Re-run any time; it's stateless.

## Daily Worker (Cloudflare)

```powershell
npm install -g wrangler   # if not installed
wrangler login
wrangler kv namespace create SIGNAL_KV     # paste returned id into wrangler.toml
wrangler secret put YT_API_KEY
wrangler secret put DISCORD_WEBHOOK_URL    # Discord: channel → Integrations → Webhooks → New
wrangler secret put RUN_TOKEN              # any random string
wrangler deploy
```

Test immediately without waiting for the cron:

```powershell
curl -H "x-run-token: YOUR_TOKEN" https://signal-recon.<your-subdomain>.workers.dev/run
```

### Editing the watchlist (no redeploy)

```powershell
wrangler kv key put --binding SIGNAL_KV watchlist '["@airevolutionx","@TheAiGrid","@theAIsearch","@intheworldofai","@newoutlier"]' --remote
```

Handles for the four §1 targets are best-guess — the CLI run will confirm them (a wrong handle prints `FAILED — channel not found`; fix it in config.json and the KV watchlist).

### Cron & DST

`wrangler.toml` is set to `0 11 * * *` (07:00 EDT). When DST ends in November, change to `0 12 * * *` and redeploy.

## What lands in Discord each morning

- Outlier videos (≥3× channel median) with VPH, length, links
- Recurring title formulas mined from the outliers
- Buyer-intent terms with **zero or thin coverage** across all targets — the open lane
- Per-channel medians and new-upload counts
