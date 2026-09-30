"""Load committed replay datasets (data/replays/) and state adapters (data/adapters/)."""
import json
from dataclasses import dataclass
from functools import lru_cache

from app.canonical import Asset, DatasetMeta, StateConfig, Village
from app.config import REPO_ROOT

REPLAYS_DIR = REPO_ROOT / "data" / "replays"
ADAPTERS_DIR = REPO_ROOT / "data" / "adapters"


@dataclass(frozen=True)
class Grid:
    lat_max: float
    lon_min: float
    cell_deg: float
    rows: int
    cols: int

    def lat(self, r: int) -> float:
        return self.lat_max - (r + 0.5) * self.cell_deg

    def lon(self, c: int) -> float:
        return self.lon_min + (c + 0.5) * self.cell_deg

    def index(self, lat: float, lon: float) -> int | None:
        r = int((self.lat_max - lat) / self.cell_deg)
        c = int((lon - self.lon_min) / self.cell_deg)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r * self.cols + c
        return None

    @property
    def bbox(self) -> dict:
        return {"lat_min": round(self.lat_max - self.rows * self.cell_deg, 4), "lat_max": self.lat_max,
                "lon_min": self.lon_min, "lon_max": round(self.lon_min + self.cols * self.cell_deg, 4)}


@dataclass
class BaseLayers:
    grid: Grid
    coast: dict
    elevation_m: list[float]
    water: list[int]
    sea: list[int]
    dist_inland_km: list[float]
    dist_channel_km: list[float]
    metadata: DatasetMeta


@dataclass
class Replay:
    replay_id: str
    scenario: dict
    base: BaseLayers
    villages: list[Village]
    assets: list[Asset]
    roads: dict
    observed_flood: dict
    state: StateConfig
    metadata: dict[str, DatasetMeta]

    @property
    def code(self) -> str:
        return self.scenario["code"]

    def step(self, step: str) -> dict:
        for s in self.scenario["steps"]:
            if s["step"] == step:
                return s
        raise KeyError(step)


def _read(path) -> dict:
    return json.loads(path.read_text())


@lru_cache
def state_configs() -> dict[str, StateConfig]:
    out = {}
    for p in sorted(ADAPTERS_DIR.glob("*.json")):
        cfg = StateConfig.model_validate(_read(p))
        out[cfg.state] = cfg
    return out


def adapt_villages(raw: list[dict], cfg: StateConfig) -> list[Village]:
    """State adapter: map state-specific field names onto the canonical Village model."""
    inverse = {state_key: canon for canon, state_key in cfg.village_field_map.items()}
    return [Village.model_validate({inverse.get(k, k): v for k, v in row.items()}) for row in raw]


@lru_cache
def load_replay(replay_id: str) -> Replay:
    d = REPLAYS_DIR / replay_id
    if not (d / "scenario.json").exists():
        raise KeyError(replay_id)
    scenario = _read(d / "scenario.json")
    grid_raw = _read(d / "base_grid.json")
    villages_raw = _read(d / "villages.json")
    assets_raw = _read(d / "assets.json")
    roads = _read(d / "roads.json")
    observed = _read(d / "observed_flood.json")
    cfg = state_configs()[scenario["state"]]
    base = BaseLayers(
        grid=Grid(**grid_raw["grid"]), coast=grid_raw["coast"], elevation_m=grid_raw["elevation_m"],
        water=grid_raw["water"], sea=grid_raw["sea"], dist_inland_km=grid_raw["dist_inland_km"],
        dist_channel_km=grid_raw["dist_channel_km"], metadata=DatasetMeta(**grid_raw["metadata"]),
    )
    return Replay(
        replay_id=replay_id, scenario=scenario, base=base,
        villages=adapt_villages(villages_raw["villages"], cfg),
        assets=[Asset.model_validate(a) for a in assets_raw["assets"]],
        roads=roads, observed_flood=observed, state=cfg,
        metadata={
            "scenario": DatasetMeta(**scenario["metadata"]), "base_grid": base.metadata,
            "villages": DatasetMeta(**villages_raw["metadata"]), "assets": DatasetMeta(**assets_raw["metadata"]),
            "roads": DatasetMeta(**roads["metadata"]), "observed_flood": DatasetMeta(**observed["metadata"]),
        },
    )


def list_replays() -> list[dict]:
    out = []
    for d in sorted(REPLAYS_DIR.iterdir()):
        if (d / "scenario.json").exists():
            r = load_replay(d.name)
            out.append({
                "replay_id": r.replay_id, "code": r.code, "cyclone_name": r.scenario["cyclone_name"],
                "state": r.state.state, "state_name": r.state.state_name, "district": r.scenario["district"],
                "landfall_time": r.scenario["landfall_time"], "languages": r.state.languages,
                "steps": [{"step": s["step"], "hours_before_landfall": s["hours_before_landfall"],
                           "issued_at": s["issued_at"], "scenario_id": f"{r.code}-{s['step']}"}
                          for s in r.scenario["steps"]],
                "metadata": r.metadata["scenario"].model_dump(),
            })
    return out


def parse_scenario_id(scenario_id: str) -> tuple[Replay, dict]:
    """'FANI-2019-T72' -> (replay, step)."""
    for item in list_replays():
        prefix = item["code"] + "-"
        if scenario_id.startswith(prefix):
            replay = load_replay(item["replay_id"])
            return replay, replay.step(scenario_id[len(prefix):])
    raise KeyError(scenario_id)
