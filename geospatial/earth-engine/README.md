# Earth Engine scripts (`tatraksha_ee/`)

Used by `services/api/app/geospatial/earth_engine.py` **only when `EARTH_ENGINE_PROJECT` is set**
(plus Earth Engine credentials: `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login`).
Without it, the API uses the committed synthetic grids in `data/replays/<replay>/base_grid.json`
and every screen shows the **Demo mode** badge. Results are cached in `data/cache/ee/` (gitignored).

| Module | What it does | Datasets |
|---|---|---|
| `layers.py` | Samples elevation and permanent water onto the replay grid; GPM rainfall accumulation | `COPERNICUS/DEM/GLO30`, `JRC/GSW1_4/GlobalSurfaceWater`, `NASA/GPM_L3/IMERG_V07` |
| `surge.py` | Bathtub surge inundation at DEM resolution, served as map tiles (`/api/scenarios/{id}/hazards/ee-tiles`) | GLO-30, JRC GSW |
| `exposure.py` | Population and building counts within 1.5 km of each village | `WorldPop/GP/100m/pop` (2020), `GOOGLE/Research/open-buildings/v3/polygons` |

Pre-sample a replay's layers: `cd services/api && EARTH_ENGINE_PROJECT=<project> uv run python ../../geospatial/earth-engine/run_replay_layers.py fani-2019`

## Screening surge model — assumptions (label: "Screening estimate – defer to official surge guidance")

The same transparent formula runs in Python (`services/api/app/surge/model.py`) and in Earth Engine:

```
peak surge S = 0.01 m/hPa × (1010 − Pc)        inverse barometer
             + 4.2e-4 × V² × shelf_factor        wind set-up (V = max sustained wind at landfall, m/s)
along-coast   g(s) = exp(−((s − Rmw)/2.5Rmw)²) right of track; 0.45·exp(−(s/1.5Rmw)²) left
water level   W = tide + S·g(s);   inland  W_in = W − decay × distance_inland_km
inundation    DEM < W_in AND connected to the sea (8-connected, through rivers/lagoons)
expected      central track, expected tide
high          max over the central half of the track set, +10 % pressure deficit, +5 % wind, high tide
```

| Parameter | Fani 2019 (Puri) | Amphan 2020 (Sundarbans) | Basis |
|---|---|---|---|
| shelf factor | 1.0 | 3.4 | steep Odisha shelf vs very shallow head-Bay shelf (sample calibration) |
| Rmw | 25 km | 30 km | typical radius of maximum winds |
| tide expected / high | 0.6 / 1.0 m | 1.0 / 1.4 m | sample (Amphan landfall near spring tide) |
| inland decay | 0.25 m/km | 0.08 m/km | sample; flat tidal delta keeps surge further inland |

Calibration check: Fani landfall (944 hPa, 175 km/h) gives ≈1.65 m surge (IMD guidance "about 1.5 m");
Amphan (968 hPa, 160 km/h) gives ≈3.2 m surge + tide (IMD guidance "about 4–5 m"). This is a screening
tool, not a hydrodynamic model (no ADCIRC/SLOSH); official surge guidance always takes precedence and
can replace it behind the same interface.

## Rainfall flood likelihood — demo heuristic

Logistic model of 72 h rainfall, low-lying terrain, drainage proximity and antecedent wetness
(`services/api/app/flood_model/model.py`). The PRD's Vertex AI model trained on Sentinel-1 flood extents
is **not built yet**; it would replace `likelihood()` with the same inputs.

## Synthetic terrain (demo mode)

`data/transformations/build_replays.py` generates a coast-distance elevation ramp with river channels,
a Chilika lagoon (Odisha) and embankments along tidal channels (West Bengal). It is a stand-in so the
pipeline runs offline; it does not match real terrain and is labelled `is_synthetic: true`.
