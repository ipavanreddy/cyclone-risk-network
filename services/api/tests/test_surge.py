from app import pipeline
from app.replays import load_replay
from app.surge import model


def test_peak_surge_formula_is_transparent():
    # 1 cm/hPa inverse barometer + C_w V^2 shelf
    s = model.peak_surge_m(944, 180, 1.0)
    assert abs(s - (0.66 + 4.2e-4 * 50.0**2)) < 1e-9


def test_calibration_matches_official_guidance_order():
    fani = model.peak_surge_m(944, 175, 1.0)  # IMD guidance ~1.5 m
    amphan = model.peak_surge_m(968, 160, 3.4)  # IMD guidance ~4-5 m (incl. tide)
    assert 1.2 < fani < 2.0
    assert 2.8 < amphan < 4.0
    assert model.peak_surge_m(900, 250, 1.0) > fani  # stronger storm -> higher surge


def test_profile_peaks_right_of_track():
    assert model.profile(25, 25) == 1.0
    assert model.profile(-25, 25) < model.profile(25, 25)
    assert model.profile(400, 25) < 0.01


def test_inundation_is_connected_and_monotonic():
    base = load_replay("fani-2019").base
    lf = {"lat": 19.8, "lon": 85.83, "heading": (0.3, 0.95)}
    p = model.SurgeParams(rmw_km=25, shelf_factor=1.0, tide_expected_m=0.6, tide_high_m=1.0,
                          inland_decay_m_per_km=0.25)
    low, _ = model.inundation(base, lf, 1.0, 0.6, p)
    high, _ = model.inundation(base, lf, 3.0, 0.6, p)
    assert sum(d > 0 for d in high) > sum(d > 0 for d in low) > 0
    # land only, never sea cells
    assert all(d == 0 for d, s in zip(high, base.sea) if s)
    # every flooded cell touches sea/water or another flooded cell (connectivity)
    g = base.grid
    for i, d in enumerate(high):
        if d > 0:
            r, c = divmod(i, g.cols)
            neigh = [(r + a) * g.cols + (c + b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                     if (a or b) and 0 <= r + a < g.rows and 0 <= c + b < g.cols]
            assert any(base.water[j] or high[j] > 0 for j in neigh)


def test_pipeline_surge_labelled_and_high_ge_expected():
    r = pipeline.run("FANI-2019-T24")
    assert r["surge"]["label"] == "Screening estimate – defer to official surge guidance"
    assert r["surge"]["peak_surge_high_m"] >= r["surge"]["peak_surge_expected_m"]
    assert r["surge"]["inundated_km2_high"] >= r["surge"]["inundated_km2_expected"] > 0
    assert r["surge"]["model_name"] and r["surge"]["model_version"]


def test_amphan_surge_larger_than_fani():
    fani = pipeline.run("FANI-2019-T24")["surge"]
    amphan = pipeline.run("AMPHAN-2020-T24")["surge"]
    assert amphan["peak_surge_expected_m"] > fani["peak_surge_expected_m"]
    assert amphan["inundated_km2_expected"] > fani["inundated_km2_expected"]
