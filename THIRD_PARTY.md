# Third-party datasets, models and libraries

Every reused dataset, model, library, service and map tile source is cited here (hackathon rule).
Licences are as published by each project at the time of the hackathon.

## AI models

| Name | Provider / licence | Used for |
|---|---|---|
| Gemini 3.7 Flash (`gemini-3.7-flash`, via Vertex AI `global`; model id from `GEMINI_MODEL`) | Google, Google Cloud / Gemini API terms | Bulletin → structured track, multimodal situation report (hazard-map PNG + bulletin + exposure tables), English advisory drafts |
| Cloud Text-to-Speech voices (en-IN, bn-IN) | Google Cloud terms | Voice advisories |
| Cloud Speech-to-Text v1 (en-IN, bn-IN, or-IN) | Google Cloud terms | Read-back check of generated advisory audio |
| Cloud Translation v2 (NMT) | Google Cloud terms | Back-translation of Odia/Bengali advisories for the human reviewer |

No other pretrained models are used. Surge, flood-likelihood, wind (modified Rankine vortex) and Village Risk are
transparent formulas written for this project (see `geospatial/earth-engine/README.md`).

## Google Cloud and Maps services (used only when configured)

| Name | Terms | Used for |
|---|---|---|
| Vertex AI (Gemini) / Gemini API | Google Cloud / Gemini API ToS | See AI models |
| Google Earth Engine | Earth Engine ToS | DEM/water/rainfall/population/buildings sampling, surge inundation tiles |
| Google Maps JavaScript API (basemap tiles "Map data © Google") | Google Maps Platform ToS | Basemap when `NEXT_PUBLIC_MAPS_API_KEY` is set |
| Google Maps Routes API, Geocoding API | Google Maps Platform ToS | Village → shelter drive time (normal conditions), village locality |
| Cloud Translation, Text-to-Speech, Speech-to-Text | Google Cloud ToS | Multilingual review, voice advisories, audio read-back |
| BigQuery | Google Cloud ToS | `audit_log`, `dispatch_log` event tables |
| Cloud Storage | Google Cloud ToS | Archive of map renders, CAP XML, advisory audio; Gemini parse cache |
| Firestore (Firebase) | Google Cloud / Firebase ToS | Record store (when a database exists) |
| Cloud Run, Cloud Build, Artifact Registry, Secret Manager | Google Cloud ToS | Hosting, image builds, secrets |
| Twilio (test credentials) / Telegram Bot API | Provider ToS | Sandbox SMS / messaging dispatch (simulated when not configured) |

## Map tiles and datasets

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| OpenStreetMap tiles & data | ODbL 1.0 (data), OSMF tile usage policy | https://www.openstreetmap.org/copyright | Basemap fallback (attribution shown on map) |
| Copernicus GLO-30 DEM | Copernicus DEM licence (free, attribution) | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30 | Elevation (Earth Engine mode) |
| JRC Global Surface Water v1.4 | CC-BY 4.0 (EC JRC / Google) | https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater | Permanent water (Earth Engine mode) |
| NASA GPM IMERG V07 | NASA open data | https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07 | Rainfall accumulation (Earth Engine mode) |
| WorldPop 100 m population (2020) | CC-BY 4.0 | https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop | Village population (Earth Engine mode) |
| Google Open Buildings v3 | CC-BY 4.0 / ODbL | https://sites.research.google/open-buildings/ | Building counts (Earth Engine mode) |
| IMD / RSMC New Delhi public reports on Cyclones Fani (2019) and Amphan (2020) | Public information | https://rsmcnewdelhi.imd.gov.in | Facts used to reconstruct the **sample** replay tracks and bulletins (landfall place/time, intensity, surge guidance). Not redistributed; replay data are approximations. |
| IMD track-forecast error statistics (order of magnitude) | Public information | https://mausam.imd.gov.in | Cone radius table (sample values) |

## Standards

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| OASIS Common Alerting Protocol (CAP) 1.2 | OASIS open standard | https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html | Advisory message format and validation |

## Frontend libraries (apps/*)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| Next.js 16 | MIT | https://nextjs.org | Dashboards (standalone server on Cloud Run) |
| React 19 / React DOM | MIT | https://react.dev | UI |
| TypeScript | Apache-2.0 | https://www.typescriptlang.org | Type checking |
| Tailwind CSS 4 + @tailwindcss/postcss | MIT | https://tailwindcss.com | Styling |
| tw-animate-css | MIT | https://github.com/Wombosvideo/tw-animate-css | Animations |
| shadcn/ui (+ `shadcn` CLI) | MIT | https://ui.shadcn.com | UI components |
| Base UI (`@base-ui/react`) | MIT | https://base-ui.com | Component primitives |
| class-variance-authority | Apache-2.0 | https://cva.style | Component variants |
| cn | MIT | https://www.npmjs.com/package/cn | Class-name helper |
| lucide-react | ISC | https://lucide.dev | Icons |
| sonner | MIT | https://sonner.emilkowal.ski | Toasts |
| next-themes | MIT | https://github.com/pacocoursey/next-themes | Theme handling |
| Leaflet 1.9 | BSD-2-Clause | https://leafletjs.com | Map fallback when no/invalid Google Maps key |
| @types/leaflet, @types/node, @types/react, @types/react-dom | MIT | https://github.com/DefinitelyTyped/DefinitelyTyped | Type definitions |
| ESLint 9 + eslint-config-next | MIT | https://eslint.org | Linting |
| Geist / Geist Mono fonts (via `next/font/google`) | SIL OFL 1.1 | https://vercel.com/font | Typography |

## Backend libraries (services/api)

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| FastAPI | MIT | https://fastapi.tiangolo.com | API |
| Uvicorn | BSD-3-Clause | https://www.uvicorn.org | ASGI server |
| Pydantic / pydantic-settings | MIT | https://docs.pydantic.dev | Schemas (AI output validation, canonical model), settings |
| python-multipart | Apache-2.0 | https://github.com/Kludex/python-multipart | Form parsing |
| Google Gen AI SDK (`google-genai`) | Apache-2.0 | https://github.com/googleapis/python-genai | Gemini calls (Vertex AI / API key) |
| earthengine-api | Apache-2.0 | https://github.com/google/earthengine-api | Earth Engine scripts |
| firebase-admin | Apache-2.0 | https://github.com/firebase/firebase-admin-python | Firestore store adapter |
| google-cloud-bigquery | Apache-2.0 | https://github.com/googleapis/python-bigquery | Audit/dispatch event sink |
| google-cloud-storage | Apache-2.0 | https://github.com/googleapis/python-storage | Media archive |
| httpx | BSD-3-Clause | https://www.python-httpx.org | Maps/Translation/TTS/STT/Twilio/Telegram REST calls |
| pytest | MIT | https://pytest.org | Tests |
| Ruff | MIT | https://docs.astral.sh/ruff | Python linting |

## Tooling and container images

| Name | Licence | Source URL | Used for |
|---|---|---|---|
| uv | Apache-2.0 / MIT | https://github.com/astral-sh/uv | Python env + image (`ghcr.io/astral-sh/uv`) |
| pnpm | MIT | https://pnpm.io | JS workspace |
| python:3.12-slim, node:22-slim | PSF / MIT (+ Debian) | https://hub.docker.com/_/python, https://hub.docker.com/_/node | Base images |
| python-pptx | MIT | https://github.com/scanny/python-pptx | Generates the pitch deck (`docs/pitch/build_deck.py`) |

## Sample / synthetic data created for this project

All in `data/replays/`, generated by `data/transformations/build_replays.py` and labelled `is_sample`
(and `is_synthetic` where applicable): reconstructed tracks and bulletins, synthetic terrain grid,
village populations and vulnerability indices, shelter/substation/hospital locations, simplified road
network, "observed" flood flags for validation, and parametric policies. Village names are real places
with approximate coordinates; codes are `SAMPLE-*` (not real LGD codes). Advisory templates in Odia and
Bengali are sample translations pending native-speaker review.
