"""Standalone: pre-sample Earth Engine layers for a replay (writes data/cache/ee/, gitignored).

  cd services/api && EARTH_ENGINE_PROJECT=<gcp-project> uv run python ../../geospatial/earth-engine/run_replay_layers.py fani-2019
"""
import json
import sys
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from tatraksha_ee import layers  # noqa: E402

if __name__ == "__main__":
    import os

    replay_id = sys.argv[1] if len(sys.argv) > 1 else "fani-2019"
    ee.Initialize(project=os.environ["EARTH_ENGINE_PROJECT"])
    g = json.loads((ROOT / "data" / "replays" / replay_id / "base_grid.json").read_text())["grid"]
    out = ROOT / "data" / "cache" / "ee"
    out.mkdir(parents=True, exist_ok=True)
    res = layers.sample_base_layers(g["lat_max"], g["lon_min"], g["cell_deg"], g["rows"], g["cols"])
    (out / f"{replay_id}-base.json").write_text(json.dumps(res))
    print(f"wrote {out / (replay_id + '-base.json')}")
