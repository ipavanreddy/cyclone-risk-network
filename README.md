# TatRaksha: Cyclone Anticipatory Action & Early-Warning Platform

Build with AI (Google) hackathon, Track 5. Full spec: [docs/PRD.md](docs/PRD.md).

## Core journey (build this first; PRD §57)

```text
Replay Scenario + Gemini Bulletin Parsing
 ↓
Surge + Flood Hazards (Earth Engine)
 ↓
Exposure + Village Risk + Shelter Cut-off
 ↓
Gemini 3.7 Flash Situation Report
 ↓
Advisory Draft + Approval + CAP
```

**Headline score:** Village Risk (Surge 30 · Rainfall flood 25 · Wind 15 · Population 15 · Vulnerability 15)
**Users:** District Disaster Management Officer (`apps/district-dashboard`) · State EOC Officer (`apps/state-eoc-dashboard`)
**Languages:** English, Odia, Bengali
**Demo states:** Odisha / Fani 2019 replay, West Bengal / Amphan 2020 replay, Andhra Pradesh (rainfall flooding)

## Stack

Next.js + TypeScript + Tailwind + shadcn/ui (pnpm workspace) · FastAPI on Cloud Run (uv, Python 3.12) ·
Gemini API / Vertex AI · BigQuery · Firebase · Cloud Storage · Google Maps Platform · Earth Engine ·
Speech-to-Text / Text-to-Speech / Translation · region `asia-south1`.

## Run locally

```bash
cp .env.example .env                      # keys optional – everything falls back to labelled demo mode
for a in apps/*; do cp $a/.env.example $a/.env.local; done
pnpm install
(cd services/api && uv sync)

pnpm dev:api                    # http://localhost:8050  (docs at /docs)
pnpm dev:district-dashboard     # http://localhost:3050  District Disaster Management Officer
pnpm dev:state-eoc-dashboard    # http://localhost:3051  State EOC Officer
pnpm test:api                   # pytest incl. a demo-mode end-to-end journey
```

Deep links for demos: `http://localhost:3050/?replay=fani-2019&step=0&tab=sitrep`
(`replay` = `fani-2019` | `amphan-2020`, `step` = 0..3 for T-72/48/24/6 h, `tab` = forecast | villages | assets | sitrep | advisories).

## 5-minute demo (PRD §44) – works with no keys

1. **District dashboard**, Odisha · Fani 2019, slider at **T-72h**. Forecast tab: bulletin parsed into a
   track table (Gemini, or the deterministic demo parser), official surge guidance; click **Verify track**.
   Map: track, uncertainty cone, forecast landfall.
2. Move the slider T-72 → T-48 → T-24 → T-6: each step is a new (sample) bulletin; hazards and risk re-run.
   Map layers: screening surge (expected / high case, labelled), rain-flood likelihood, wind swath.
3. **Village risk** tab: ranked villages with the 30/25/15/15/15 breakdown; **Assets**: exposed substations,
   hospitals, shelters, roads cut and shelters cut off from the relief depot.
4. **Sitrep** tab → *Generate*: structured report (headline, key numbers, actions by role with deadlines,
   priority villages, shelters, uncertainties). Gemini gets the hazard-map PNG + bulletin + exposure tables;
   every number is validated against the data. The image sent to the model is shown.
5. **Advisories** tab: draft an **Odia** advisory for the top village → ▶ audio preview → tick
   *Translation reviewed* → **Approve** → **View CAP 1.2** → **Dispatch (sandbox)**.
6. **State EOC dashboard** (:3051): both states side by side, block comparison, parametric trigger
   estimates (sample policies) with post-event verification, predicted-vs-observed validation, advisory
   and dispatch logs, audit trail. Switch to **West Bengal · Amphan 2020** (Bengali, surge up tidal
   channels) to show the same canonical structure via the state adapter.

## Real integrations vs demo mode

Every integration is real when its env var is set and falls back to a **labelled demo mode** otherwise.
The "Demo mode · N fallbacks" badge (top right of both dashboards) lists what is running in demo mode;
`GET /api/status` returns the same. `FORCE_DEMO_MODE=true` forces demo mode (used by tests).

| Integration | Env vars | Demo-mode fallback |
|---|---|---|
| Gemini (bulletin parse, multimodal sitrep, advisory drafts) | `GEMINI_API_KEY` (or `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT`), model from `GEMINI_MODEL` | Deterministic regex parser; template sitrep/advisories built from the same data |
| Earth Engine (DEM, JRC water, GPM rain, WorldPop, Open Buildings, surge tiles) | `EARTH_ENGINE_PROJECT` + `GOOGLE_APPLICATION_CREDENTIALS` / ADC | Committed synthetic grid + parametric rainfall in `data/replays/` |
| Google Maps basemap | `NEXT_PUBLIC_MAPS_API_KEY` in `apps/*/.env.local` | Leaflet + OpenStreetMap |
| Cloud Translation + Text-to-Speech | `GOOGLE_CLOUD_API_KEY` | Pre-approved en/or/bn templates; browser speech-synthesis preview |
| Firestore (records) | `FIREBASE_PROJECT_ID` | Local SQLite at `services/api/.data/` |
| BigQuery (audit/dispatch events) | `GOOGLE_CLOUD_PROJECT`, `BIGQUERY_DATASET` (table `audit_log`) | Local store only |
| SMS sandbox (Twilio test creds) | `SMS_SANDBOX_KEY=SID:TOKEN`, `SMS_SANDBOX_FROM`, `SMS_SANDBOX_TO` | Simulated, logged |
| Messaging sandbox (Telegram bot) | `MESSAGING_SANDBOX_TOKEN`, `MESSAGING_SANDBOX_CHAT_ID` | Simulated, logged |

Replay data (tracks, bulletins, villages, shelters, assets, roads) are always **sample data**, labelled in
the data (`metadata.is_sample`) and in the UI. Regenerate with
`cd services/api && uv run python ../../data/transformations/build_replays.py`.
Model assumptions: [geospatial/earth-engine/README.md](geospatial/earth-engine/README.md).

## Known gaps

- Rainfall flood likelihood is a transparent heuristic; the Vertex AI model trained on Sentinel-1 extents is not built.
- Surge is a screening bathtub model (labelled); terrain is synthetic until Earth Engine is enabled.
- Odia/Bengali templates are sample translations that need native-speaker review; voice calls are simulated.
- Earth Engine / Firestore / BigQuery / Twilio / Telegram / Translation code paths are untested against live services (no keys).
- Andhra Pradesh (rainfall-flooding) replay and live-forecast mode are not built. The API Dockerfile copies only `app/`; it also needs `data/` and `ai/`.

## Layout

| Path | Purpose |
|---|---|
| `apps/district-dashboard/` | District Disaster Management Officer app |
| `apps/state-eoc-dashboard/` | State EOC Officer dashboard |
| `services/api/` | FastAPI gateway (all domain logic starts here as modules) |
| `services/forecast-ingest/` | IMD bulletin + weather ingestion, Gemini bulletin parsing |
| `services/surge/` | Storm surge estimation (Earth Engine) |
| `services/flood-model/` | Rainfall flood-likelihood model (Vertex AI) |
| `services/exposure/` | Exposure, Village Risk, road/shelter cut-off |
| `services/situation-reasoning/` | Gemini 3.7 Flash multimodal situation reports |
| `services/advisories-cap/` | Advisory drafting, approval, CAP XML, sandbox dispatch |
| `services/parametric/` | Parametric insurance trigger calculations (sample policies) |
| `services/localization/` | Speech-to-Text, Text-to-Speech, Translation |
| `ai/` | Versioned prompts (`prompts/*_v1.md`), JSON schemas exported from Pydantic (`uv run python -m app.ai.export_schemas`) |
| `data/` | Canonical schema (`schemas/`), state adapters (`adapters/`), replay datasets (`replays/`), generator (`transformations/`) |
| `geospatial/earth-engine/` | Earth Engine scripts + model assumptions |
| `infrastructure/` | Cloud Run, BigQuery, Firebase config |
| `docs/` | PRD and architecture notes |
