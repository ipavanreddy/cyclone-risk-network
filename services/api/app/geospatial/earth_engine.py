"""Earth Engine adapter. Real mode (EARTH_ENGINE_PROJECT set) samples real layers onto the replay grid
using the scripts in geospatial/earth-engine/tatraksha_ee/; demo mode returns None and callers keep the
committed synthetic layers. Results are cached under data/cache/ee/ (gitignored)."""
import importlib
import json
import sys
from dataclasses import replace
from datetime import datetime
from functools import lru_cache

from app import integrations
from app.canonical import DatasetMeta
from app.config import REPO_ROOT, settings

EE_DIR = REPO_ROOT / "geospatial" / "earth-engine"
CACHE_DIR = REPO_ROOT / "data" / "cache" / "ee"


def _ee_module(name: str):
    if str(EE_DIR) not in sys.path:
        sys.path.insert(0, str(EE_DIR))
    return importlib.import_module(f"tatraksha_ee.{name}")


@lru_cache
def _init() -> bool:
    import ee

    ee.Initialize(project=settings.earth_engine_project)
    return True


def _cached(key: str, fn):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    value = fn()
    path.write_text(json.dumps(value))
    return value


def enrich_base(replay):
    """Replace synthetic elevation/water with Copernicus DEM + JRC water. None in demo mode."""
    if not integrations.earth_engine_enabled():
        return None
    try:
        _init()
        layers = _ee_module("layers")
        g = replay.base.grid
        sampled = _cached(f"{replay.replay_id}-base", lambda: layers.sample_base_layers(g.lat_max, g.lon_min,
                                                                                        g.cell_deg, g.rows, g.cols))
        integrations.clear_error("earth_engine")
        base = replay.base
        water = [1 if (w or s) else 0 for w, s in zip(sampled["water"], base.sea)]
        elevation = [base.elevation_m[i] if water[i] else sampled["elevation_m"][i] for i in range(len(water))]
        meta = DatasetMeta(source="Earth Engine: COPERNICUS/DEM/GLO30 + JRC/GSW1_4/GlobalSurfaceWater (occurrence>50%)",
                           reference_timestamp=datetime.now().isoformat(timespec="seconds"),
                           dataset_version="GLO30 2021 / GSW 1.4", geographic_scope=base.metadata.geographic_scope,
                           is_sample=False, is_synthetic=False)
        return replace(base, elevation_m=elevation, water=water, metadata=meta)
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("earth_engine", exc)
        return None


def gpm_rainfall(replay, start: datetime, end: datetime) -> list[float] | None:
    """GPM IMERG accumulated rainfall (mm) per grid cell for the replay window. None in demo mode."""
    if not integrations.earth_engine_enabled():
        return None
    try:
        _init()
        layers = _ee_module("layers")
        g = replay.base.grid
        key = f"{replay.replay_id}-gpm-{start:%Y%m%d%H}-{end:%Y%m%d%H}"
        return _cached(key, lambda: layers.sample_gpm(g.lat_max, g.lon_min, g.cell_deg, g.rows, g.cols,
                                                      start.isoformat(), end.isoformat()))
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("earth_engine", exc)
        return None


def village_exposure(replay) -> dict[str, dict] | None:
    """WorldPop population + Open Buildings count within 1.5 km of each village. None in demo mode."""
    if not integrations.earth_engine_enabled():
        return None
    try:
        _init()
        exposure = _ee_module("exposure")
        pts = [{"id": v.village_code, "lat": v.lat, "lon": v.lon} for v in replay.villages]
        return _cached(f"{replay.replay_id}-exposure", lambda: exposure.village_exposure(pts, 1500))
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("earth_engine", exc)
        return None


def inundation_tiles(replay, landfall_lat: float, landfall_lon: float, water_level_m: float,
                     decay_m_per_km: float) -> dict | None:
    """Earth Engine bathtub inundation rendered as XYZ map tiles. None in demo mode."""
    if not integrations.earth_engine_enabled():
        return None
    try:
        _init()
        surge = _ee_module("surge")
        bb = replay.base.grid.bbox
        return surge.inundation_tile_url(bb, water_level_m, decay_m_per_km)
    except Exception as exc:  # noqa: BLE001
        integrations.record_error("earth_engine", exc)
        return None
