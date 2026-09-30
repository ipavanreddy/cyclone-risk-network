import pytest

from app.forecast_ingest.parser import parse_bulletin
from app.replays import load_replay


@pytest.mark.parametrize("replay_id", ["fani-2019", "amphan-2020"])
def test_parser_matches_truth_for_every_bulletin(replay_id):
    replay = load_replay(replay_id)
    for step in replay.scenario["steps"]:
        p = parse_bulletin(step["bulletin_text"])
        truth = step["truth_parse"]
        assert p.cyclone_name == truth["cyclone_name"]
        assert p.issued_at == truth["issued_at"]
        assert len(p.track) == len(truth["track"])
        for a, b in zip(p.track, truth["track"]):
            assert (a.time, a.lat, a.lon, a.max_wind_kmh, a.central_pressure_hpa) == (
                b["time"], b["lat"], b["lon"], b["max_wind_kmh"], b["central_pressure_hpa"])
        assert p.expected_landfall.area == truth["expected_landfall"]["area"]
        assert p.official_surge_text and truth["official_surge_text"] in p.official_surge_text
        assert p.requires_human_review


def test_parser_never_invents_values():
    p = parse_bulletin("Some unrelated text without a track table or landfall information at all.")
    assert p.track == []
    assert p.cyclone_name == "unknown"
    assert p.confidence == 0
