"""Road cut-off analysis (PRD §14): remove flooded road segments and check shelter reachability.

An edge is cut if any point sampled every ~1 km along it has expected surge depth ≥ 0.3 m or
rainfall flood likelihood ≥ 0.8. A shelter is "safe" if its own cell is not flooded by the same
rule. Villages route (Dijkstra) to the nearest safe shelter within 30 km. A shelter is "cut off"
if it can no longer be reached from the district relief depot (hub) for pre-stocking/relief.
"""
import heapq
from collections import defaultdict

from app.geo import km

CUT_SURGE_M = 0.3
CUT_FLOOD_P = 0.8
MAX_EVAC_KM = 30.0


def cell_flooded(grid, surge: list[float], flood: list[float], lat: float, lon: float) -> bool:
    i = grid.index(lat, lon)
    return i is not None and (surge[i] >= CUT_SURGE_M or flood[i] >= CUT_FLOOD_P)


def edge_cut(grid, surge, flood, a: dict, b: dict) -> bool:
    n = max(2, int(km(a["lat"], a["lon"], b["lat"], b["lon"])) + 1)
    for k in range(n + 1):
        f = k / n
        if cell_flooded(grid, surge, flood, a["lat"] + f * (b["lat"] - a["lat"]), a["lon"] + f * (b["lon"] - a["lon"])):
            return True
    return False


def _graph(edges: list[dict], cut: set[str]) -> dict[str, list[tuple[str, float]]]:
    g: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for e in edges:
        if e["edge_id"] in cut:
            continue
        g[e["from"]].append((e["to"], e["length_km"]))
        g[e["to"]].append((e["from"], e["length_km"]))
    return g


def dijkstra(g, src: str, limit: float = 1e9) -> dict[str, float]:
    dist = {src: 0.0}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) or d > limit:
            continue
        for v, w in g.get(u, []):
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def analyse(grid, roads: dict, surge: list[float], flood: list[float], hub_id: str,
            shelter_ids: list[str], village_ids: list[str]) -> dict:
    nodes = {n["id"]: n for n in roads["nodes"]}
    cut = {e["edge_id"] for e in roads["edges"]
           if edge_cut(grid, surge, flood, nodes[e["from"]], nodes[e["to"]])}
    g_open = _graph(roads["edges"], cut)
    g_base = _graph(roads["edges"], set())
    safe = {s for s in shelter_ids if not cell_flooded(grid, surge, flood, nodes[s]["lat"], nodes[s]["lon"])}
    from_hub = dijkstra(g_open, hub_id)
    from_hub_base = dijkstra(g_base, hub_id)
    cut_off = [s for s in shelter_ids if s in from_hub_base and s not in from_hub]
    villages = {}
    for v in village_ids:
        dist = dijkstra(g_open, v, MAX_EVAC_KM)
        options = sorted((dist[s], s) for s in safe if s in dist and dist[s] <= MAX_EVAC_KM)
        villages[v] = {"shelter_reachable": bool(options),
                       "nearest_reachable_shelter": options[0][1] if options else None,
                       "shelter_distance_km": round(options[0][0], 1) if options else None}
    cut_edges = [e for e in roads["edges"] if e["edge_id"] in cut]
    return {
        "cut_edges": [{"edge_id": e["edge_id"], "road": e["road"], "from": e["from"], "to": e["to"],
                       "kind": e["kind"]} for e in cut_edges],
        "roads_cut": sorted({e["road"] for e in cut_edges if e["kind"] == "arterial"}),
        "safe_shelters": sorted(safe),
        "cut_off_shelters": cut_off,
        "villages": villages,
        "rule": f"Edge cut if expected surge ≥ {CUT_SURGE_M} m or flood likelihood ≥ {CUT_FLOOD_P} along it; "
                f"evacuation routing ≤ {MAX_EVAC_KM:.0f} km to a safe shelter; cut-off = unreachable from relief depot.",
    }
