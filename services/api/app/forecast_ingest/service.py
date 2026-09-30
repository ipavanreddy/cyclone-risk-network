"""Bulletin parsing: Gemini (bulletin_parse_v1) with deterministic parser fallback and cross-check."""
import hashlib
import json
from datetime import UTC, datetime
from functools import lru_cache

from app import integrations, media
from app.ai import orchestrator
from app.ai.schemas import BulletinParse
from app.config import settings
from app.forecast_ingest.parser import parse_bulletin
from app.store import audit, get_store


def _plausible(p: BulletinParse) -> bool:
    return bool(p.track) and all(0 < t.lat < 35 and 70 < t.lon < 100 and 0 < t.max_wind_kmh < 400 for t in p.track)


def discrepancies(ai: BulletinParse, ref: BulletinParse) -> list[str]:
    """Compare Gemini output with the deterministic parse; anything listed needs officer attention."""
    out = []
    if len(ai.track) != len(ref.track):
        out.append(f"track rows: AI {len(ai.track)} vs parser {len(ref.track)}")
    for a, b in zip(ai.track, ref.track):
        if abs(a.lat - b.lat) > 0.15 or abs(a.lon - b.lon) > 0.15 or abs(a.max_wind_kmh - b.max_wind_kmh) > 10:
            out.append(f"{b.time}: AI ({a.lat},{a.lon},{a.max_wind_kmh}) vs parser ({b.lat},{b.lon},{b.max_wind_kmh})")
    return out


def parse(text: str) -> dict:
    reference = parse_bulletin(text)
    result, prov, mode = orchestrator.run(
        "bulletin_parse", "v1", f"BULLETIN TEXT:\n<<<\n{text}\n>>>", BulletinParse, lambda: reference)
    notes: list[str] = []
    if mode == "gemini":
        if not _plausible(result):
            notes.append("Gemini output failed plausibility checks; deterministic parse used instead.")
            result = reference
        else:
            notes += discrepancies(result, reference)
    return {
        "parse": result.model_dump(),
        "mode": mode,
        "provenance": prov.model_dump(mode="json"),
        "cross_check": {"method": "deterministic regex parser", "discrepancies": notes},
        "requires_human_review": True,
    }


@lru_cache(maxsize=64)
def _cached_parse(text: str) -> dict:
    """In-memory cache, backed by Cloud Storage for Gemini parses so Cloud Run cold starts do not re-call Gemini
    for the same bulletin (key = bulletin text + model + prompt version)."""
    key = hashlib.sha256(f"{settings.gemini_model}|bulletin_parse_v1|{text}".encode()).hexdigest()[:24]
    path = f"cache/bulletin-parse/{key}.json"
    if integrations.gemini_enabled() and media.exists(path):
        cached = media.download(path)
        if cached:
            return json.loads(cached)
    result = parse(text)
    if result["mode"] == "gemini":
        media.upload(path, json.dumps(result), "application/json")
    return result


def parse_for_scenario(scenario_id: str, text: str) -> dict:
    """Parse once per scenario (cached); the pipeline uses the verified track if one exists."""
    return _cached_parse(text)


def verify_track(scenario_id: str, verified_by: str, role: str, track: list[dict] | None, parsed: dict) -> dict:
    doc = {
        "scenario_id": scenario_id,
        "verified_by": verified_by,
        "role": role,
        "verified_at": datetime.now(UTC).isoformat(),
        "track": track or parsed["parse"]["track"],
        "edited": track is not None,
    }
    get_store().put("track_verifications", scenario_id, doc)
    audit("track_verified", verified_by, role, {"id": scenario_id, "edited": doc["edited"]})
    return doc


def get_verification(scenario_id: str) -> dict | None:
    return get_store().get("track_verifications", scenario_id)
