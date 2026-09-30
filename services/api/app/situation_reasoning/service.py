"""Situation report (PRD §15, §33): Gemini multimodal (hazard map PNG + bulletin + exposure tables)
with a deterministic template fallback. All numbers are validated against the pipeline output."""
import json
import uuid
from datetime import datetime

from google.genai import types

from app.ai import orchestrator
from app.ai.schemas import (
    AdvisoryDraftBrief,
    KeyNumbers,
    PriorityVillage,
    RoleAction,
    ShelterNote,
    SituationReport,
)
from app.render import LEGEND, hazard_png
from app.store import audit, get_store

STAGE_LABEL = {"watch": "Cyclone Watch", "warning": "Cyclone Warning", "evacuation_order": "Evacuation Order",
               "final_warning": "Final Warning"}


def _deadline(nominal: int, hours_left: float) -> int:
    """Nominal deadline (hours before landfall), pulled forward if already passed."""
    return nominal if nominal < hours_left else max(1, int(hours_left) - 2)


def _fmt_time(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%d %b %Y %H:%M IST")


def context_for(result: dict) -> dict:
    """Structured context handed to Gemini. Everything numeric comes from here."""
    sc = result["scenario"]
    return {
        "scenario": {k: sc[k] for k in ("scenario_id", "cyclone_name", "state_name", "district", "stage",
                                        "forecast_issued_at", "hours_to_forecast_landfall", "forecast_landfall",
                                        "track_verified", "issuing_authority")},
        "key_numbers": result["key_numbers"],
        "surge": {k: result["surge"][k] for k in ("label", "peak_surge_expected_m", "peak_surge_high_m",
                                                  "inundated_km2_expected", "inundated_km2_high", "assumptions")},
        "official_surge_guidance": result["bulletin"]["parse"].get("official_surge_text"),
        "flood": {k: result["flood"][k] for k in ("label", "max_rain_72h_mm", "rain_source")},
        "cone_radius_at_landfall_km": result["track"]["cone_radius_at_landfall_km"],
        "villages_top": [{k: v[k] for k in ("village_code", "name", "block", "population", "risk_score", "risk_band",
                                            "surge_depth_expected_m", "surge_depth_high_m", "flood_likelihood",
                                            "max_wind_kmh", "shelter_reachable", "nearest_reachable_shelter",
                                            "gale_arrival_hours_before_landfall")}
                         for v in result["villages"][:15]],
        "exposed_assets": [{k: a.get(k) for k in ("asset_id", "type", "name", "hazards", "capacity", "safe",
                                                  "cut_off", "assigned_evacuees", "over_capacity")}
                           for a in result["assets"] if a["exposed"] or a.get("cut_off") or a.get("over_capacity")],
        "roads_cut": result["network"]["roads_cut"],
        "action_templates": ["District Authority", "Power Utility", "Health", "Police", "Fisheries", "Municipal / Relief"],
    }


def demo_report(result: dict) -> SituationReport:
    sc, kn = result["scenario"], result["key_numbers"]
    hrs = sc["hours_to_forecast_landfall"]
    lf = sc["forecast_landfall"]
    high = [v for v in result["villages"] if v["risk_band"] in ("High", "Very High")]
    shelters = [a for a in result["assets"] if a["type"] == "shelter"]
    cut_off = [a for a in shelters if a["cut_off"]]
    over = [a for a in shelters if a.get("over_capacity")]
    # shelters are wind-rated; flag only water hazards
    exposed_sh = [a for a in shelters if not a["cut_off"] and not a.get("over_capacity")
                  and any(h != "wind" for h in a["hazards"])]
    subs = [a for a in result["assets"] if a["type"] == "substation" and a["exposed"]]
    safe_subs = [a for a in result["assets"] if a["type"] == "substation" and not a["exposed"]]
    hosp = [a for a in result["assets"] if a["type"] == "hospital" and a["exposed"]]
    safe_shelters = [a for a in shelters if a["safe"] and not a["cut_off"]]
    surge = result["surge"]
    actions = [
        RoleAction(role="District Authority",
                   action=f"Evacuate {len(high)} priority villages ({', '.join(v['name'] for v in high[:6]) or 'none'}); "
                          f"open {len(safe_shelters)} safe shelters; arrange alternatives for "
                          f"{len(cut_off) + len(over)} cut-off or over-capacity shelters.",
                   deadline_hours_before_landfall=_deadline(48, hrs),
                   evidence=[f"villages_high_risk = {kn['villages_high_risk']}",
                             f"people_high_risk = {kn['people_high_risk']}",
                             f"evacuation_demand = {kn['evacuation_demand']}"]),
        RoleAction(role="Power Utility",
                   action=f"Prepare pre-emptive shutdown at {len(subs)} exposed substations "
                          f"({', '.join(a['name'].split(' substation')[0] for a in subs[:4]) or 'none'}); stage "
                          f"restoration crews at {min(3, len(safe_subs))} substations outside the hazard zone.",
                   deadline_hours_before_landfall=_deadline(6, hrs),
                   evidence=[f"substations_exposed = {kn['substations_exposed']}",
                             f"max wind {result['wind']['max_kmh']:.0f} km/h"]),
        RoleAction(role="Health",
                   action=f"Transfer dialysis, maternity and critical patients from {len(hosp)} exposed health "
                          f"facilities ({', '.join(a['name'].split(' (')[0] for a in hosp[:3]) or 'none'}).",
                   deadline_hours_before_landfall=_deadline(24, hrs),
                   evidence=[f"hospitals_exposed = {kn['hospitals_exposed']}"]),
        RoleAction(role="Fisheries",
                   action="Recall all boats and prohibit fishing; secure boats and nets above the high-case surge line.",
                   deadline_hours_before_landfall=_deadline(48, hrs),
                   evidence=[f"peak screening surge {surge['peak_surge_expected_m']} m (high {surge['peak_surge_high_m']} m)"]),
        RoleAction(role="Police",
                   action=f"Manage evacuation traffic and close roads likely to be cut: "
                          f"{', '.join(result['network']['roads_cut']) or 'none flagged yet'}.",
                   deadline_hours_before_landfall=_deadline(24, hrs),
                   evidence=[f"roads_cut = {kn['roads_cut']}"]),
        RoleAction(role="Municipal / Relief",
                   action=f"Pre-stock food, water and medicines at shelters, prioritising {len(cut_off)} shelters "
                          "that lose road access to the relief depot.",
                   deadline_hours_before_landfall=_deadline(24, hrs),
                   evidence=[f"shelters_cut_off = {kn['shelters_cut_off']}",
                             f"reachable_shelter_capacity = {kn['reachable_shelter_capacity']}"]),
    ]
    notes = [ShelterNote(asset_id=a["asset_id"], name=a["name"], issue="cut off from relief depot by flooded roads",
                         recommendation="Pre-stock for 72 h now or redirect evacuees to a connected shelter")
             for a in cut_off]
    notes += [ShelterNote(asset_id=a["asset_id"], name=a["name"],
                          issue=f"over capacity ({a['assigned_evacuees']} assigned vs {a['capacity']})",
                          recommendation="Open schools/public buildings nearby as overflow") for a in over]
    notes += [ShelterNote(asset_id=a["asset_id"], name=a["name"],
                          issue=f"inside hazard zone ({', '.join(h for h in a['hazards'] if h != 'wind')})",
                          recommendation="Use upper floors only; confirm structural safety") for a in exposed_sh[:5]]
    unc = [
        f"Landfall position uncertainty ±{result['track']['cone_radius_at_landfall_km']} km (typical forecast error).",
        f"{surge['label']}: official guidance says '{result['bulletin']['parse'].get('official_surge_text') or 'n/a'}'.",
        result["flood"]["label"] + ".",
        "Villages, shelters, assets and roads are sample data for this replay.",
    ]
    if not sc["track_verified"]:
        unc.append("Forecast track not yet verified by the officer.")
    top = high[0] if high else result["villages"][0]
    names = {a["asset_id"]: a["name"].replace(" (sample)", "") for a in shelters}
    top_shelter = names.get(top["nearest_reachable_shelter"] or "", "the nearest safe building")
    stage = sc["stage"]
    drafts = [AdvisoryDraftBrief(
        audience="public", language="en", stage=stage,
        text=f"{STAGE_LABEL[stage]}: Cyclone {sc['cyclone_name']} expected near {sc['district']} around "
             f"{_fmt_time(lf['time'])}. Residents of {top['name']} move to {top_shelter}. "
             f"Issued by {sc['issuing_authority']}.")]
    return SituationReport(
        headline=f"{sc['cyclone_name']}: forecast landfall in ~{hrs:.0f} h ({_fmt_time(lf['time'])}), winds up to "
                 f"{lf['max_wind_kmh']} km/h; {kn['people_high_risk']:,} people in {kn['villages_high_risk']} "
                 f"High/Very High risk villages; screening surge up to {surge['peak_surge_expected_m']} m "
                 f"(high case {surge['peak_surge_high_m']} m).",
        confidence="medium" if hrs > 30 else "high",
        key_numbers=KeyNumbers(**kn),
        actions=actions,
        priority_villages=[PriorityVillage(village_code=v["village_code"], name=v["name"], risk_score=v["risk_score"],
                                           reason=", ".join(f"{k} {p}" for k, p in sorted(v["contributions"].items(),
                                                                                         key=lambda x: -x[1])[:2]))
                           for v in high[:10]],
        shelters_attention=notes,
        uncertainties=unc,
        advisory_drafts=drafts,
    )


def validate(report: SituationReport, result: dict) -> tuple[SituationReport, list[str]]:
    """Ground every number: key numbers must equal the data; villages/shelters must exist."""
    corrections = []
    truth = result["key_numbers"]
    for k, v in report.key_numbers.model_dump().items():
        if truth[k] != v:
            corrections.append(f"key_numbers.{k}: model said {v}, data says {truth[k]} (corrected)")
    report.key_numbers = KeyNumbers(**truth)
    by_code = {v["village_code"]: v for v in result["villages"]}
    kept = []
    for pv in report.priority_villages:
        v = by_code.get(pv.village_code)
        if v is None:
            corrections.append(f"priority village {pv.village_code} not in data (removed)")
            continue
        if pv.risk_score != v["risk_score"]:
            corrections.append(f"{v['name']} risk {pv.risk_score} -> {v['risk_score']} (corrected)")
            pv.risk_score = v["risk_score"]
        kept.append(pv)
    report.priority_villages = kept
    ids = {a["asset_id"] for a in result["assets"]}
    dropped = [s.asset_id for s in report.shelters_attention if s.asset_id not in ids]
    if dropped:
        corrections.append(f"unknown shelters removed: {dropped}")
    report.shelters_attention = [s for s in report.shelters_attention if s.asset_id in ids]
    return report, corrections


def generate(result: dict, requested_by: str = "system", role: str = "District Disaster Management Officer") -> dict:
    sc = result["scenario"]
    png = hazard_png(result)
    ctx = context_for(result)
    context = ("STRUCTURED CONTEXT (the only source of numbers):\n" + json.dumps(ctx, default=str) +
               "\n\nOFFICIAL BULLETIN:\n<<<\n" + result["bulletin"]["text"] + "\n>>>\n\n" + LEGEND)
    parts = [types.Part.from_bytes(data=png, mime_type="image/png")]
    report, prov, mode = orchestrator.run("sitrep", "v1", context, SituationReport,
                                          lambda: demo_report(result), parts)
    report, corrections = validate(report, result)
    rid = f"SITREP-{sc['scenario_id']}-{uuid.uuid4().hex[:6]}"
    record = {
        "report_id": rid, "scenario_id": sc["scenario_id"], **report.model_dump(),
        "generated_at": prov.generated_at.isoformat(), "model_name": prov.model_name,
        "model_version": prov.model_version, "prompt_version": prov.prompt_version, "mode": mode,
        "inputs": {"hazard_map_png": f"/api/scenarios/{sc['scenario_id']}/hazards.png",
                   "bulletin_no": sc["bulletin_no"], "image_bytes": len(png),
                   "multimodal": True, "context_fields": list(ctx.keys())},
        "validation": {"numbers_grounded": True, "corrections": corrections},
        "requires_human_review": True,
    }
    get_store().put("sitreps", rid, record)
    audit("sitrep_generated", requested_by, role, {"id": rid, "mode": mode, "model": prov.model_name})
    return record


def latest(scenario_id: str) -> dict | None:
    items = get_store().list("sitreps", scenario_id=scenario_id)
    return items[-1] if items else None
