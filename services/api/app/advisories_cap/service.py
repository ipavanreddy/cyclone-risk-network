"""Advisory lifecycle (PRD §16): draft (template / Gemini) → human approval → CAP 1.2 → sandbox dispatch → log."""
import json
import uuid
from datetime import UTC, datetime, timedelta, timezone

from app import media
from app.advisories_cap import cap, dispatch, templates
from app.ai import orchestrator
from app.ai.schemas import AdvisoryDraft
from app.store import audit, bigquery_log, get_store

DDMO = "District Disaster Management Officer"
STATE_EOC = "State EOC Officer"
ROLES = {DDMO, STATE_EOC}
IST = timezone(timedelta(hours=5, minutes=30))
MANDATORY = ["what", "where", "when", "action", "shelter", "authority"]


class AdvisoryError(ValueError):
    pass


def _when(result: dict, village: dict) -> str:
    lf = datetime.fromisoformat(result["scenario"]["forecast_landfall"]["time"])
    gale = village.get("gale_arrival_hours_before_landfall")
    t = lf - timedelta(hours=gale) if gale is not None else lf
    return t.astimezone(IST).strftime("%d-%m-%Y %H:%M IST")


def missing_fields(fields: dict, text: str, shelter_name: str | None, authority: str) -> list[str]:
    missing = [k for k in MANDATORY if not str(fields.get(k, "")).strip()]
    if authority not in text:
        missing.append("authority (not in text)")
    if shelter_name and shelter_name not in text:
        missing.append("shelter (not in text)")
    return missing


def draft(result: dict, village_code: str, audience: str, language: str, stage: str | None,
          requested_by: str, role: str) -> dict:
    sc = result["scenario"]
    if language not in templates.LANGUAGES:
        raise AdvisoryError(f"language must be one of {list(templates.LANGUAGES)}")
    village = next((v for v in result["villages"] if v["village_code"] == village_code), None)
    if village is None:
        raise AdvisoryError(f"unknown village {village_code}")
    stage = stage or sc["stage"]
    if stage not in templates.STAGES:
        raise AdvisoryError(f"stage must be one of {templates.STAGES}")
    shelters = {a["asset_id"]: a for a in result["assets"]}
    shelter = shelters.get(village["nearest_reachable_shelter"] or "")
    shelter_name = (f"{shelter['name'].replace(' (sample)', '')} ({village['shelter_distance_km']} km)"
                    if shelter else None)
    where = f"{village['name']}, {village['block']} block, {sc['district']}"
    authority = sc["issuing_authority"]
    kwargs = dict(name=sc["cyclone_name"], where=where, when=_when(result, village),
                  wind_kmh=village["max_wind_kmh"], surge_m=village["surge_depth_expected_m"],
                  flood_p=village["flood_likelihood"], shelter=shelter_name, authority=authority)
    template = templates.render(language, stage, audience, **kwargs)

    mode, prov_d, notes = "template", None, []
    if language == "en":
        ctx = {"stage": stage, "audience": audience, "approved_template": template, "village": {
            k: village[k] for k in ("name", "block", "risk_score", "risk_band", "surge_depth_expected_m",
                                    "flood_likelihood", "max_wind_kmh", "nearest_reachable_shelter")}}
        ai, prov, ai_mode = orchestrator.run("advisory", "v1", "CONTEXT:\n" + json.dumps(ctx), AdvisoryDraft,
                                             lambda: AdvisoryDraft.model_validate(template))
        prov_d = prov.model_dump(mode="json")
        miss = missing_fields(ai.fields.model_dump(), ai.text, shelter_name, authority)
        if ai_mode == "gemini" and not miss:
            template, mode = ai.model_dump(), "gemini"
        elif ai_mode == "gemini":
            notes.append(f"Gemini draft rejected (missing mandatory fields: {miss}); approved template used.")
    else:
        prov_d = orchestrator.demo_provenance("advisory_v1").model_dump(mode="json")
        prov_d["model_name"] = "approved-template"
    miss = missing_fields(template["fields"], template["text"], shelter_name, authority)
    if miss:
        raise AdvisoryError(f"mandatory fields missing: {miss}")
    aid = f"ADV-{sc['scenario_id']}-{uuid.uuid4().hex[:6].upper()}"
    record = {
        "advisory_id": aid, "scenario_id": sc["scenario_id"], "state": sc["state"], "district": sc["district"],
        "stage": stage, "audience": audience, "language": language,
        "language_name": templates.LANGUAGES[language], "village_code": village_code,
        "area": {"name": where, "lat": village["lat"], "lon": village["lon"], "radius_km": 3.0},
        "risk_score": village["risk_score"], "risk_band": village["risk_band"],
        "headline": template["headline"], "fields": template["fields"], "text": template["text"],
        "draft_mode": mode, "review_note": templates.REVIEW_NOTE[language], "notes": notes,
        "cap_xml": None, "audio_url": None, "status": "draft", "approved_by": None, "approved_at": None,
        "sent_at": None, "created_at": datetime.now(UTC).isoformat(), "created_by": requested_by,
        "model_name": prov_d["model_name"], "model_version": prov_d["model_version"],
        "prompt_version": prov_d["prompt_version"],
    }
    get_store().put("advisories", aid, record)
    audit("advisory_drafted", requested_by, role, {"id": aid, "language": language, "mode": mode})
    return record


def get(aid: str) -> dict:
    rec = get_store().get("advisories", aid)
    if rec is None:
        raise KeyError(aid)
    return rec


def approve(aid: str, approved_by: str, role: str, edited_text: str | None, translation_reviewed: bool,
            result: dict) -> dict:
    rec = get(aid)
    if role != DDMO:
        raise AdvisoryError(f"only the {DDMO} can approve advisories")
    if not approved_by.strip():
        raise AdvisoryError("approved_by is required")
    if rec["status"] != "draft":
        raise AdvisoryError(f"advisory is already {rec['status']}")
    if rec["language"] != "en" and not translation_reviewed:
        raise AdvisoryError("non-English advisory: confirm the translation was reviewed (translation_reviewed=true)")
    if edited_text:
        authority = result["scenario"]["issuing_authority"]
        if authority not in edited_text:
            raise AdvisoryError("edited text must keep the issuing authority")
        rec["text"] = edited_text
        rec["edited"] = True
    now = datetime.now(IST)
    sc = result["scenario"]
    replay_note = (f"Replay exercise of Cyclone {sc['cyclone_name']} ({sc['scenario_id']}); sample data; "
                   "onset refers to the replay forecast.")
    rec["cap_xml"] = cap.build(
        identifier=f"TATRAKSHA-{aid}", sender=_state_sender(result), sent=now, status="Exercise", stage=rec["stage"],
        risk_band=rec["risk_band"], language=templates.CAP_LANG[rec["language"]], headline=rec["headline"],
        description=f"{rec['fields']['what']} – {rec['fields']['when']}", instruction=rec["text"],
        sender_name=sc["issuing_authority"], area_desc=rec["area"]["name"], lat=rec["area"]["lat"],
        lon=rec["area"]["lon"], radius_km=rec["area"]["radius_km"], onset=sc["forecast_landfall"]["time"],
        geocode=("SAMPLE_VILLAGE_CODE", rec["village_code"]), note=replay_note)
    errors = cap.validate(rec["cap_xml"])
    if errors:
        raise AdvisoryError(f"CAP validation failed: {errors}")
    rec["cap_gcs_uri"] = media.upload(f"cap/{aid}.xml", rec["cap_xml"], "application/cap+xml")
    rec.update({"status": "approved", "approved_by": approved_by, "approved_role": role,
                "approved_at": now.isoformat(), "translation_reviewed": translation_reviewed})
    get_store().put("advisories", aid, rec)
    audit("advisory_approved", approved_by, role, {"id": aid, "edited": bool(edited_text)})
    return rec


def _state_sender(result: dict) -> str:
    from app.replays import state_configs

    return state_configs()[result["scenario"]["state"]].cap_sender


def dispatch_advisory(aid: str, channels: list[str], dispatched_by: str, role: str) -> dict:
    rec = get(aid)
    if role not in ROLES:
        raise AdvisoryError(f"role must be one of {sorted(ROLES)}")
    if rec["status"] not in ("approved", "sent"):
        raise AdvisoryError("advisory must be approved by the District Disaster Management Officer before dispatch")
    bad = [c for c in channels if c not in dispatch.CHANNELS]
    if bad or not channels:
        raise AdvisoryError(f"channels must be a non-empty subset of {dispatch.CHANNELS}")
    now = datetime.now(UTC).isoformat()
    entries = []
    for ch in channels:
        res = dispatch.send(ch, rec["text"], rec["cap_xml"])
        entry = {"log_id": f"{aid}-{ch}-{uuid.uuid4().hex[:4]}", "advisory_id": aid, "scenario_id": rec["scenario_id"],
                 "state": rec["state"], "language": rec["language"], "village_code": rec["village_code"],
                 "at": now, "by": dispatched_by, "role": role, **res}
        get_store().put("dispatch_log", entry["log_id"], entry)
        bigquery_log("dispatch_log", {k: entry.get(k) for k in (
            "log_id", "advisory_id", "scenario_id", "state", "language", "village_code", "channel", "provider",
            "status", "simulated", "role")} | {"event_time": now, "dispatched_by": dispatched_by})
        entries.append(entry)
    rec.update({"status": "sent", "sent_at": now})
    get_store().put("advisories", aid, rec)
    audit("advisory_dispatched", dispatched_by, role, {"id": aid, "channels": channels,
                                                       "simulated": [e["channel"] for e in entries if e["simulated"]]})
    return {"advisory": rec, "dispatch": entries}


def list_advisories(scenario_id: str | None = None, state: str | None = None) -> list[dict]:
    return get_store().list("advisories", scenario_id=scenario_id, state=state)
