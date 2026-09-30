"""Advisory, CAP, dispatch, localization, state and platform-status endpoints (PRD §37)."""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app import integrations, pipeline
from app.advisories_cap import service as adv
from app.advisories_cap.dispatch import CHANNELS
from app.localization import service as loc
from app.replays import list_replays, state_configs
from app.store import get_store

router = APIRouter(prefix="/api", tags=["advisories"])


class DraftIn(BaseModel):
    scenario_id: str
    village_code: str
    audience: str = "public"
    language: str = "en"
    stage: str | None = None
    requested_by: str = "District Disaster Management Officer (demo)"
    role: str = adv.DDMO


class ApproveIn(BaseModel):
    approved_by: str
    role: str = adv.DDMO
    edited_text: str | None = None
    translation_reviewed: bool = False


class DispatchIn(BaseModel):
    channels: list[str] = CHANNELS
    dispatched_by: str
    role: str = adv.DDMO


class TranslateIn(BaseModel):
    text: str
    target: str
    source: str = "en"


class TtsIn(BaseModel):
    text: str
    language: str = "en"


def _err(exc: Exception):
    if isinstance(exc, KeyError):
        raise HTTPException(404, f"not found: {exc}") from None
    if isinstance(exc, adv.AdvisoryError):
        raise HTTPException(409 if "already" in str(exc) or "must be approved" in str(exc) else 400, str(exc)) from None
    raise exc


@router.post("/advisories/draft")
def draft(body: DraftIn) -> dict:
    try:
        result = pipeline.run(body.scenario_id)
        return adv.draft(result, body.village_code, body.audience, body.language, body.stage, body.requested_by,
                         body.role)
    except (KeyError, adv.AdvisoryError) as exc:
        _err(exc)


@router.get("/advisories")
def list_advisories(scenario: str | None = None, state: str | None = None) -> list[dict]:
    return adv.list_advisories(scenario, state)


@router.get("/advisories/{aid}")
def get_advisory(aid: str) -> dict:
    try:
        return adv.get(aid)
    except KeyError as exc:
        _err(exc)


@router.post("/advisories/{aid}/approve")
def approve(aid: str, body: ApproveIn) -> dict:
    try:
        rec = adv.get(aid)
        return adv.approve(aid, body.approved_by, body.role, body.edited_text, body.translation_reviewed,
                           pipeline.run(rec["scenario_id"]))
    except (KeyError, adv.AdvisoryError) as exc:
        _err(exc)


@router.post("/advisories/{aid}/dispatch")
def dispatch(aid: str, body: DispatchIn) -> dict:
    try:
        return adv.dispatch_advisory(aid, body.channels, body.dispatched_by, body.role)
    except (KeyError, adv.AdvisoryError) as exc:
        _err(exc)


@router.get("/advisories/{aid}/cap")
def cap_xml(aid: str) -> Response:
    try:
        rec = adv.get(aid)
    except KeyError as exc:
        _err(exc)
    if not rec["cap_xml"]:
        raise HTTPException(409, "CAP message is generated on approval")
    return Response(rec["cap_xml"], media_type="application/cap+xml")


@router.get("/alerts/feed")
def alert_feed(state: str | None = None) -> list[dict]:
    sent = [a for a in adv.list_advisories(state=state) if a["status"] == "sent"]
    return [{"advisory_id": a["advisory_id"], "headline": a["headline"], "language": a["language"],
             "sent_at": a["sent_at"], "cap_url": f"/api/advisories/{a['advisory_id']}/cap"} for a in sent]


@router.get("/dispatch-log")
def dispatch_log(state: str | None = None, scenario: str | None = None) -> list[dict]:
    return get_store().list("dispatch_log", state=state, scenario_id=scenario)


@router.get("/audit-log")
def audit_log() -> list[dict]:
    return get_store().list("audit_log")


@router.post("/translate")
def translate(body: TranslateIn) -> dict:
    return loc.translate(body.text, body.target, body.source)


@router.post("/text-to-speech")
def tts(body: TtsIn) -> dict:
    return loc.text_to_speech(body.text, body.language)


@router.get("/status")
def status() -> dict:
    return integrations.status()


@router.get("/states")
def states() -> list[dict]:
    return [cfg.model_dump() for cfg in state_configs().values()]


@router.get("/states/{state_id}/analytics")
def state_analytics(state_id: str, step: str | None = None) -> dict:
    cfg = state_configs().get(state_id.upper())
    if cfg is None:
        raise HTTPException(404, f"unknown state {state_id}")
    out = []
    for rp in [r for r in list_replays() if r["state"] == cfg.state]:
        s = next((x for x in rp["steps"] if x["step"] == step), rp["steps"][0])
        r = pipeline.run(s["scenario_id"])
        blocks: dict[str, dict] = {}
        for v in r["villages"]:
            b = blocks.setdefault(v["block"], {"block": v["block"], "villages": 0, "population": 0,
                                               "people_high_risk": 0, "max_risk": 0, "no_shelter": 0})
            b["villages"] += 1
            b["population"] += v["population"]
            b["max_risk"] = max(b["max_risk"], v["risk_score"])
            b["no_shelter"] += 0 if v["shelter_reachable"] else 1
            if v["risk_band"] in ("High", "Very High"):
                b["people_high_risk"] += v["population"]
        advs = adv.list_advisories(state=cfg.state)
        out.append({"replay_id": rp["replay_id"], "scenario_id": s["scenario_id"], "district": r["scenario"]["district"],
                    "cyclone_name": rp["cyclone_name"], "stage": r["scenario"]["stage"],
                    "hours_to_forecast_landfall": r["scenario"]["hours_to_forecast_landfall"],
                    "key_numbers": r["key_numbers"], "blocks": sorted(blocks.values(), key=lambda b: -b["max_risk"]),
                    "advisories": {st: sum(1 for a in advs if a["status"] == st) for st in ("draft", "approved", "sent")}})
    return {"state": cfg.model_dump(), "districts": out}
