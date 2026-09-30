# forecast-ingest

IMD bulletin + weather ingestion, Gemini bulletin parsing

Starts as a router/module in `services/api/app/` (e.g. `app/forecast_ingest/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
