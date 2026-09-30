from app.exposure import risk


def test_weights_sum_to_100_points_at_max():
    f = {k: 1.0 for k in risk.DEFAULT_WEIGHTS}
    s, contrib = risk.score(f)
    assert s == 100
    assert contrib == {"surge": 30.0, "flood": 25.0, "wind": 15.0, "population": 15.0, "vulnerability": 15.0}


def test_zero_hazard_zero_score():
    s, _ = risk.score({k: 0.0 for k in risk.DEFAULT_WEIGHTS})
    assert s == 0


def test_factor_normalisation():
    f = risk.factors(surge_expected_m=2.0, surge_high_m=2.0, flood_likelihood=0.5, max_wind_kmh=62,
                     population=500, vulnerability_index=0.4, shelter_reachable=True)
    assert f == {"surge": 1.0, "flood": 0.5, "wind": 0.0, "population": 0.0, "vulnerability": 0.4}
    assert risk.factors(0, 0, 0, 300, 50000, 0.9, False)["wind"] == 1.0
    assert risk.factors(0, 0, 0, 300, 50000, 0.9, False)["population"] == 1.0
    # no reachable shelter raises vulnerability (clamped at 1)
    assert risk.factors(0, 0, 0, 0, 1000, 0.9, False)["vulnerability"] == 1.0


def test_example_weighted_score():
    # surge 0.8, flood 0.72, wind 0.9, pop 0.6, vuln 0.7 -> 24 + 18 + 13.5 + 9 + 10.5 = 75
    s, _ = risk.score({"surge": 0.8, "flood": 0.72, "wind": 0.9, "population": 0.6, "vulnerability": 0.7})
    assert s == 75
    assert risk.band(75) == "Very High"
    assert risk.band(60) == "High"
    assert risk.band(40) == "Moderate"
    assert risk.band(10) == "Low"


def test_custom_weights_are_normalised():
    s, _ = risk.score({"surge": 1, "flood": 0, "wind": 0, "population": 0, "vulnerability": 0},
                      {"surge": 1, "flood": 1, "wind": 0, "population": 0, "vulnerability": 0})
    assert s == 50
