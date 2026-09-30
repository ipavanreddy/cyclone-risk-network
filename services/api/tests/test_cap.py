from datetime import datetime, timedelta, timezone

from app.advisories_cap import cap

IST = timezone(timedelta(hours=5, minutes=30))


def _msg(**over):
    kw = dict(identifier="TATRAKSHA-ADV-1", sender="ddma@sample.invalid", sent=datetime(2019, 5, 1, 8, 30, tzinfo=IST),
              status="Exercise", stage="evacuation_order", risk_band="Very High", language="or-IN",
              headline="ସ୍ଥାନାନ୍ତରଣ ଆଦେଶ – Fani", description="wind & surge <2 m>", instruction="Go now",
              sender_name="Collector, Puri", area_desc="Penthakata, Puri", lat=19.8, lon=85.84, radius_km=3,
              onset="2019-05-03T08:30:00+05:30", geocode=("SAMPLE_VILLAGE_CODE", "SAMPLE-OD-FANI-002"), note="replay")
    kw.update(over)
    return cap.build(**kw)


def test_cap_is_valid():
    xml = _msg()
    assert cap.validate(xml) == []
    assert 'xmlns="urn:oasis:names:tc:emergency:cap:1.2"' in xml
    assert "<sent>2019-05-01T08:30:00+05:30</sent>" in xml
    assert "<responseType>Evacuate</responseType>" in xml
    assert "<severity>Extreme</severity>" in xml
    assert "<circle>19.8000,85.8400 3.0</circle>" in xml
    assert "&lt;2 m&gt;" in xml  # escaped


def test_stage_mapping():
    xml = _msg(stage="watch", risk_band="Moderate")
    assert "<urgency>Future</urgency>" in xml and "<certainty>Possible</certainty>" in xml
    assert "<severity>Moderate</severity>" in xml


def test_validator_catches_errors():
    good = _msg()
    assert cap.validate("<alert>") != []
    assert any("status" in e for e in cap.validate(good.replace("<status>Exercise", "<status>Bogus")))
    assert any("sent" in e for e in cap.validate(good.replace("2019-05-01T08:30:00+05:30</sent>", "2019-05-01T03:00:00Z</sent>")))
    missing = good.replace("<msgType>Alert</msgType>", "")
    assert any("msgType" in e for e in cap.validate(missing))
    assert any("root" in e for e in cap.validate(good.replace("cap:1.2", "cap:1.1")))
