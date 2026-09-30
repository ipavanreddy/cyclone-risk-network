import json

from app import integrations
from app.advisories_cap import dispatch
from app.ai import orchestrator
from app.ai.export_schemas import CANONICAL_PATH, SCHEMAS_DIR, render, render_canonical
from app.ai.schemas import ALL_SCHEMAS, BulletinParse
from app.geospatial import earth_engine
from app.localization import service as loc
from app.replays import REPLAYS_DIR, adapt_villages, load_replay, state_configs
from app.store import SQLiteStore


def test_status_reports_demo_mode_for_every_backend_integration():
    st = integrations.status()
    assert st["demo_mode"] is True and st["sample_data"] is True
    modes = {i["name"]: i["mode"] for i in st["integrations"]}
    assert set(modes) >= {"gemini", "earth_engine", "translation_tts", "firestore", "bigquery", "sms", "messaging"}
    assert all(m == "demo" for m in modes.values())


def test_gemini_fallback_is_labelled():
    fallback = BulletinParse(cyclone_name="X", issued_at="", track=[], expected_landfall={"area": "a", "time": "t"},
                             confidence=0.0)
    res, prov, mode = orchestrator.run("bulletin_parse", "v1", "ctx", BulletinParse, lambda: fallback)
    assert mode == "demo" and res is fallback
    assert prov.model_name == orchestrator.DEMO_MODEL_NAME
    assert prov.prompt_version == "bulletin_parse_v1"


def test_earth_engine_adapter_demo_returns_none():
    replay = load_replay("fani-2019")
    assert earth_engine.enrich_base(replay) is None
    assert earth_engine.village_exposure(replay) is None
    assert earth_engine.inundation_tiles(replay, 19.8, 85.8, 2.0, 0.25) is None


def test_earth_engine_scripts_are_importable():
    mod = earth_engine._ee_module("surge")
    assert hasattr(mod, "inundation_image") and hasattr(mod, "inundation_tile_url")
    assert hasattr(earth_engine._ee_module("layers"), "sample_base_layers")
    assert hasattr(earth_engine._ee_module("exposure"), "village_exposure")


def test_translation_and_tts_demo():
    assert loc.translate("hello", "or")["mode"] == "demo"
    t = loc.text_to_speech("hello", "bn")
    assert t["mode"] == "demo" and t["audio_url"] is None and t["language_code"] == "bn-IN"


def test_dispatch_simulated_without_tokens():
    for ch in ["sms", "messaging", "voice"]:
        r = dispatch.send(ch, "test", None)
        assert r["simulated"] is True and r["status"] == "simulated"
    assert dispatch.send("alert_feed", "t", "<x/>")["status"] == "published"


def test_sqlite_store_roundtrip(tmp_path):
    s = SQLiteStore(str(tmp_path / "s.sqlite3"))
    s.put("c", "1", {"a": 1, "k": "x"})
    s.put("c", "2", {"a": 2, "k": "y"})
    s.put("c", "1", {"a": 3, "k": "x"})
    assert s.get("c", "1") == {"a": 3, "k": "x"}
    assert [d["a"] for d in s.list("c")] == [3, 2]  # update keeps original order
    assert [d["a"] for d in s.list("c", k="y")] == [2]
    assert s.get("c", "nope") is None


def test_state_adapter_maps_wb_fields_to_canonical():
    cfg = state_configs()["WB"]
    raw = json.loads((REPLAYS_DIR / "amphan-2020" / "villages.json").read_text())
    assert "mouza_name" in raw["villages"][0]
    vs = adapt_villages(raw["villages"], cfg)
    assert vs[0].name and vs[0].village_code.startswith("SAMPLE-WB")
    assert {c.state for c in state_configs().values()} >= {"OD", "WB"}


def test_exported_schemas_are_in_sync():
    for name in ALL_SCHEMAS:
        assert (SCHEMAS_DIR / f"{name}.schema.json").read_text() == render(name), f"re-run export_schemas for {name}"
    assert CANONICAL_PATH.read_text() == render_canonical()


def test_datasets_carry_metadata():
    for rid in ["fani-2019", "amphan-2020"]:
        for meta in load_replay(rid).metadata.values():
            assert meta.source and meta.reference_timestamp and meta.dataset_version and meta.geographic_scope
            assert meta.is_sample is True
