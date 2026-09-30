"""Parametric trigger endpoints (PRD §17, §37). Sample policies; planning estimates only."""
from fastapi import APIRouter, HTTPException

from app import pipeline
from app.parametric import model
from app.replays import list_replays, load_replay, parse_scenario_id

router = APIRouter(prefix="/api", tags=["parametric"])


@router.get("/parametric/policies")
def policies(state: str | None = None) -> list[dict]:
    return [p for p in model.POLICIES if state is None or p["state"] == state]


@router.post("/scenarios/{scenario_id}/parametric")
def estimate(scenario_id: str) -> dict:
    try:
        replay, _ = parse_scenario_id(scenario_id)
    except KeyError:
        raise HTTPException(404, f"unknown scenario {scenario_id}") from None
    r = pipeline.run(scenario_id)
    return {"scenario_id": scenario_id, "label": model.LABEL,
            "estimates": model.estimate(r, replay.scenario["model_params"]["rmw_km"])}


@router.post("/parametric/{policy_id}/verify")
def verify(policy_id: str) -> dict:
    pol = next((p for p in model.POLICIES if p["policy_id"] == policy_id), None)
    if pol is None:
        raise HTTPException(404, f"unknown policy {policy_id}")
    rp = next(r for r in list_replays() if r["state"] == pol["state"])
    replay = load_replay(rp["replay_id"])
    return model.verify(pol, replay.scenario["truth_track"], replay.scenario["landfall_time"],
                        replay.scenario["model_params"]["rmw_km"])
