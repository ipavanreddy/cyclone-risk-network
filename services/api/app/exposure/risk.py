"""Village Risk score (PRD §13) — transparent weighted model, weights from the state adapter config.

  Village Risk = 100 × ( surge × 0.30 + rainfall flood × 0.25 + wind × 0.15
                         + population exposure × 0.15 + vulnerability × 0.15 )

Factor normalisation (each 0–1):
  surge        = clamp((0.7 × expected depth + 0.3 × high-case depth) / 2.0 m)
  flood        = rainfall flood likelihood (0–1)
  wind         = clamp((max sustained wind − 62 km/h) / (200 − 62))
  population   = clamp(log10(population / 500) / 2)        (500 → 0, 50 000 → 1)
  vulnerability = vulnerability index (+0.15 if no safe shelter is reachable by road), clamped
"""
import math

from app.geo import clamp

DEFAULT_WEIGHTS = {"surge": 0.30, "flood": 0.25, "wind": 0.15, "population": 0.15, "vulnerability": 0.15}
BANDS = [(75, "Very High"), (55, "High"), (35, "Moderate"), (0, "Low")]


def factors(surge_expected_m: float, surge_high_m: float, flood_likelihood: float, max_wind_kmh: float,
            population: int, vulnerability_index: float, shelter_reachable: bool) -> dict[str, float]:
    return {
        "surge": clamp((0.7 * surge_expected_m + 0.3 * surge_high_m) / 2.0),
        "flood": clamp(flood_likelihood),
        "wind": clamp((max_wind_kmh - 62.0) / (200.0 - 62.0)),
        "population": clamp(math.log10(max(population, 1) / 500.0) / 2.0),
        "vulnerability": clamp(vulnerability_index + (0.0 if shelter_reachable else 0.15)),
    }


def score(f: dict[str, float], weights: dict[str, float] | None = None) -> tuple[int, dict[str, float]]:
    """Returns (score 0–100, weighted contribution per factor in points)."""
    w = weights or DEFAULT_WEIGHTS
    total_w = sum(w.values())
    contrib = {k: round(100 * w[k] * f[k] / total_w, 1) for k in w}
    return int(round(sum(contrib.values()))), contrib


def band(s: float) -> str:
    for threshold, name in BANDS:
        if s >= threshold:
            return name
    return "Low"
