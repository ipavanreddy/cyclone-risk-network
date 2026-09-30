"""Demo-mode end-to-end journey (PRD §44): replay -> parse -> verify -> hazards -> exposure -> sitrep
-> advisory (Odia) -> approval -> CAP -> dispatch -> logs."""
from app.advisories_cap import cap


def test_full_demo_journey(client):
    sid = "FANI-2019-T48"
    # 1. replay scenario + bulletin parse
    sc = client.post("/api/scenarios", json={"replay_id": "fani-2019", "step": "T48"}).json()
    assert sc["scenario"]["scenario_id"] == sid and sc["scenario"]["track_verified"] is False
    # 2. officer verifies the track
    v = client.post(f"/api/scenarios/{sid}/track/verify", json={"verified_by": "A. Das (DDMO)"}).json()
    assert v["verified_by"] == "A. Das (DDMO)"
    assert client.get(f"/api/scenarios/{sid}").json()["scenario"]["track_verified"] is True
    # 3. hazards
    surge = client.post(f"/api/scenarios/{sid}/surge").json()
    assert surge["peak_surge_expected_m"] > 0
    # 4. exposure + village risk
    villages = client.get(f"/api/scenarios/{sid}/villages").json()
    target = villages[0]
    assert target["risk_band"] in ("High", "Very High")
    # 5. situation report (multimodal inputs recorded, numbers grounded)
    rep = client.post(f"/api/scenarios/{sid}/sitrep", json={}).json()
    kn = client.get(f"/api/scenarios/{sid}/exposure").json()["key_numbers"]
    assert rep["key_numbers"] == kn
    assert rep["model_name"] and rep["model_version"] and rep["prompt_version"] == "sitrep_v1"
    assert rep["mode"] == "demo" and rep["inputs"]["multimodal"] is True
    roles = {a["role"] for a in rep["actions"]}
    assert {"District Authority", "Power Utility", "Health"} <= roles
    assert all(a["deadline_hours_before_landfall"] < sc["scenario"]["hours_to_forecast_landfall"] for a in rep["actions"])
    assert rep["priority_villages"][0]["village_code"] == target["village_code"]
    assert client.get(f"/api/scenarios/{sid}/sitrep").json()["report_id"] == rep["report_id"]
    # 6. advisory draft in Odia
    d = client.post("/api/advisories/draft", json={"scenario_id": sid, "village_code": target["village_code"],
                                                   "language": "or", "audience": "fishers"}).json()
    assert d["status"] == "draft" and d["language"] == "or" and d["stage"] == "warning"
    assert set(d["fields"]) == {"what", "where", "when", "action", "shelter", "authority"}
    assert "ବାତ୍ୟା" in d["text"] and d["prompt_version"] == "advisory_v1"
    aid = d["advisory_id"]
    # CAP not available before approval; dispatch refused before approval
    assert client.get(f"/api/advisories/{aid}/cap").status_code == 409
    assert client.post(f"/api/advisories/{aid}/dispatch", json={"dispatched_by": "x"}).status_code == 409
    # 7. approval rules: only DDMO, translation must be reviewed
    assert client.post(f"/api/advisories/{aid}/approve",
                       json={"approved_by": "S. Roy", "role": "State EOC Officer", "translation_reviewed": True}).status_code == 400
    assert client.post(f"/api/advisories/{aid}/approve", json={"approved_by": "A. Das"}).status_code == 400
    ap = client.post(f"/api/advisories/{aid}/approve", json={"approved_by": "A. Das", "translation_reviewed": True}).json()
    assert ap["status"] == "approved" and ap["approved_by"] == "A. Das"
    assert client.post(f"/api/advisories/{aid}/approve", json={"approved_by": "A. Das", "translation_reviewed": True}).status_code == 409
    # 8. CAP 1.2
    xml = client.get(f"/api/advisories/{aid}/cap")
    assert xml.headers["content-type"].startswith("application/cap+xml")
    assert cap.validate(xml.text) == [] and "<language>or-IN</language>" in xml.text
    # 9. sandbox dispatch (simulated) + logs
    out = client.post(f"/api/advisories/{aid}/dispatch",
                      json={"channels": ["sms", "voice", "alert_feed"], "dispatched_by": "A. Das"}).json()
    assert out["advisory"]["status"] == "sent"
    assert {e["channel"]: e["simulated"] for e in out["dispatch"]} == {"sms": True, "voice": True, "alert_feed": False}
    assert len(client.get("/api/dispatch-log", params={"scenario": sid}).json()) == 3
    assert any(f["advisory_id"] == aid for f in client.get("/api/alerts/feed").json())
    events = [e["event"] for e in client.get("/api/audit-log").json()]
    for ev in ["track_verified", "sitrep_generated", "advisory_drafted", "advisory_approved", "advisory_dispatched"]:
        assert ev in events
    assert any(a["advisory_id"] == aid for a in client.get("/api/advisories", params={"scenario": sid}).json())


def test_english_advisory_and_edit_rules(client):
    sid = "AMPHAN-2020-T24"
    v = client.get(f"/api/scenarios/{sid}/villages").json()[0]
    d = client.post("/api/advisories/draft", json={"scenario_id": sid, "village_code": v["village_code"]}).json()
    assert d["language"] == "en" and "Issued by" in d["text"] and d["state"] == "WB"
    bad = client.post(f"/api/advisories/{d['advisory_id']}/approve", json={"approved_by": "B. Sen", "edited_text": "Go now."})
    assert bad.status_code == 400
    assert client.post("/api/advisories/draft", json={"scenario_id": sid, "village_code": "nope"}).status_code == 400
    assert client.post("/api/advisories/draft", json={"scenario_id": sid, "village_code": v["village_code"],
                                                      "language": "xx"}).status_code == 400
