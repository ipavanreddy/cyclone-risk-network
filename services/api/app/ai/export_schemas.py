"""Write ai/schemas/<name>.schema.json from the Pydantic models. Run: uv run python -m app.ai.export_schemas"""
import json

from app.ai.schemas import ALL_SCHEMAS
from app.canonical import Asset, DatasetMeta, StateConfig, Village
from app.config import REPO_ROOT

SCHEMAS_DIR = REPO_ROOT / "ai" / "schemas"
CANONICAL_PATH = REPO_ROOT / "data" / "schemas" / "canonical_v1.schema.json"


def render_canonical() -> str:
    defs = {m.__name__: m.model_json_schema() for m in (Village, Asset, StateConfig, DatasetMeta)}
    return json.dumps({"title": "TatRaksha canonical disaster-risk data model v1 (PRD §21, §31)",
                       "definitions": defs}, indent=2) + "\n"


def render(name: str) -> str:
    return json.dumps(ALL_SCHEMAS[name].model_json_schema(), indent=2) + "\n"


def main() -> None:
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    for name in ALL_SCHEMAS:
        (SCHEMAS_DIR / f"{name}.schema.json").write_text(render(name))
        print(f"wrote ai/schemas/{name}.schema.json")
    CANONICAL_PATH.write_text(render_canonical())
    print("wrote data/schemas/canonical_v1.schema.json")


if __name__ == "__main__":
    main()
