def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["demo_mode"] is True


def test_replays_and_states(client):
    reps = client.get("/api/replays").json()
    assert {r["replay_id"] for r in reps} == {"fani-2019", "amphan-2020"}
    assert [s["step"] for s in reps[0]["steps"]] == ["T72", "T48", "T24", "T6"]
    states = client.get("/api/states").json()
    assert {s["state"] for s in states} == {"OD", "WB"}


def test_create_and_get_scenario(client):
    r = client.post("/api/scenarios", json={"mode": "replay", "replay_id": "fani-2019", "step": "T72"})
    assert r.status_code == 200
    body = r.json()
    sc = body["scenario"]
    assert sc["scenario_id"] == "FANI-2019-T72" and sc["mode"] == "replay" and sc["stage"] == "watch"
    assert body["bulletin"]["mode"] == "demo" and body["bulletin"]["requires_human_review"]
    assert len(body["track"]["cone"]) > 10 and len(body["track"]["members"]) == sc["track_set_size"]
    assert client.get("/api/scenarios/FANI-2019-T72").json()["scenario"]["scenario_id"] == "FANI-2019-T72"
    assert client.get("/api/scenarios/NOPE-T1").status_code == 404
    assert client.post("/api/scenarios", json={"mode": "live"}).status_code == 400


def test_bulletin_parse_endpoint(client):
    text = client.get("/api/scenarios/FANI-2019-T48").json()["bulletin"]["text"]
    r = client.post("/api/bulletins/parse", json={"text": text}).json()
    assert r["parse"]["cyclone_name"] == "Fani" and len(r["parse"]["track"]) > 5
    assert r["provenance"]["prompt_version"] == "bulletin_parse_v1"
    assert client.post("/api/bulletins/parse", json={"text": "short"}).status_code == 400


def test_hazards_and_png(client):
    r = client.get("/api/scenarios/FANI-2019-T24/hazards", params=[("layer", "surge_expected"), ("layer", "flood_likelihood")])
    body = r.json()
    g = body["grid"]
    assert len(body["layers"]["surge_expected"]) == g["rows"] * g["cols"]
    assert set(body["layers"]) == {"surge_expected", "flood_likelihood"}
    assert "Screening estimate" in body["labels"]["surge"]
    assert client.get("/api/scenarios/FANI-2019-T24/hazards", params={"layer": "bogus"}).status_code == 400
    png = client.get("/api/scenarios/FANI-2019-T24/hazards.png")
    assert png.headers["content-type"] == "image/png" and png.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert client.post("/api/scenarios/FANI-2019-T24/surge").json()["label"].startswith("Screening")
    assert "flood_likelihood" not in client.post("/api/scenarios/FANI-2019-T24/flood").json()
    assert client.get("/api/scenarios/FANI-2019-T24/hazards/ee-tiles").json()["mode"] == "demo"


def test_exposure_villages_shelters(client):
    ex = client.get("/api/scenarios/FANI-2019-T24/exposure").json()
    assert ex["key_numbers"]["people_high_risk"] > 0
    vs = client.get("/api/scenarios/FANI-2019-T24/villages", params={"sort": "risk"}).json()
    scores = [v["risk_score"] for v in vs]
    assert scores == sorted(scores, reverse=True)
    top = vs[0]
    assert sum(top["contributions"].values()) == __import__("pytest").approx(top["risk_score"], abs=1)
    sh = client.get("/api/scenarios/FANI-2019-T24/shelters/reachability").json()
    assert sh["shelters"] and "rule" in sh
    assert client.get("/api/scenarios/FANI-2019-T24/exposure", params={"district": "Nowhere"}).status_code == 404


def test_validation_and_parametric(client):
    v = client.get("/api/scenarios/FANI-2019-T24/validation").json()
    assert set(v["confusion"]) == {"tp", "fp", "fn", "tn"}
    p = client.post("/api/scenarios/FANI-2019-T24/parametric").json()
    assert p["estimates"] and 0 <= p["estimates"][0]["trigger_probability"] <= 1
    assert "not a payout decision" in p["label"]
    ver = client.post("/api/parametric/PP-OD-ZA/verify").json()
    assert ver["trigger_met"] is True
    assert client.get("/api/parametric/policies", params={"state": "WB"}).json()[0]["state"] == "WB"


def test_state_analytics(client):
    a = client.get("/api/states/WB/analytics").json()
    assert a["districts"][0]["district"] == "South 24 Parganas"
    assert a["districts"][0]["blocks"]
    assert client.get("/api/states/XX/analytics").status_code == 404


def test_translate_tts_endpoints(client):
    assert client.post("/api/translate", json={"text": "hi", "target": "bn"}).json()["mode"] == "demo"
    assert client.post("/api/text-to-speech", json={"text": "hi", "language": "or"}).json()["mode"] == "demo"
