import { rasterUrl, type MapFeatures, type RGBA } from "@/components/hazard-map";
import { BAND_COLOR, fmtTime, type Asset, type Hazards, type ScenarioSummary, type Village } from "@/lib/types";

export type LayerToggles = {
  surge: boolean; surgeHigh: boolean; flood: boolean; wind: boolean; cone: boolean; members: boolean;
  villages: boolean; assets: boolean; roads: boolean;
};

export const DEFAULT_TOGGLES: LayerToggles = {
  surge: true, surgeHigh: true, flood: true, wind: false, cone: true, members: false, villages: true, assets: true, roads: true,
};

const ASSET_COLOR: Record<string, string> = { shelter: "#ffffff", substation: "#facc15", hospital: "#ec4899" };

function ramp(a: number[], b: number[], t: number, alpha: number): RGBA {
  const k = Math.max(0, Math.min(1, t));
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, alpha].map(Math.round) as RGBA;
}

export function hazardRaster(h: Hazards, t: LayerToggles): string {
  const L = h.layers;
  return rasterUrl(h.grid, (i) => {
    if (L.water?.[i]) return null;
    const se = (L.surge_expected?.[i] ?? 0) as number;
    const sh = (L.surge_high?.[i] ?? 0) as number;
    if (t.surge && se > 0) return ramp([90, 140, 255], [10, 30, 150], se / 2, 215);
    if (t.surgeHigh && sh > 0) return [120, 170, 255, 130];
    const w = (L.wind_max?.[i] ?? 0) as number;
    const p = (L.flood_likelihood?.[i] ?? 0) as number;
    if (t.flood && p >= 0.35) return ramp([170, 220, 150], [20, 110, 50], (p - 0.35) / 0.55, 150);
    if (t.wind && w >= 62) return ramp([230, 200, 240], [120, 30, 150], (w - 62) / 140, 120);
    return null;
  });
}

export function buildFeatures(
  s: ScenarioSummary,
  h: Hazards | null,
  villages: Village[],
  assets: Asset[],
  t: LayerToggles,
  selected: string | null,
  tileUrl?: string | null,
): MapFeatures {
  const b = s.grid.bbox;
  const bounds: [[number, number], [number, number]] = [[b.lat_min, b.lon_min], [b.lat_max, b.lon_max]];
  const f: MapFeatures = { bounds, images: [], polygons: [], lines: [], points: [], tileUrl };
  if (h) f.images.push({ url: hazardRaster(h, t), bounds, opacity: 1 });
  if (t.cone) f.polygons.push({ latlngs: s.track.cone, style: { color: "#555", fill: "#888", fillOpacity: 0.12, weight: 1, dash: "4 4" } });
  if (t.members)
    for (const m of s.track.members) f.lines.push({ latlngs: m.line, style: { color: "#666", weight: 1, opacity: 0.5 } });
  f.lines.push({ latlngs: s.track.points.map((p) => [p.lat, p.lon]), style: { color: "#111", weight: 2.5 }, tooltip: "Forecast track (bulletin)" });
  for (const p of s.track.points)
    f.points.push({ lat: p.lat, lon: p.lon, radius: 3, style: { color: "#111", fill: "#111" },
      tooltip: `${fmtTime(p.time)} · ${p.max_wind_kmh} km/h · ${p.category ?? ""}` });
  if (t.roads)
    for (const r of s.network.roads)
      f.lines.push({ latlngs: r.coords, style: r.cut ? { color: "#dc2626", weight: 4, dash: "6 4" } : { color: "#6b7280", weight: r.kind === "arterial" ? 2 : 1, opacity: 0.7 },
        tooltip: `${r.road}${r.cut ? " – CUT (flooded)" : ""}` });
  if (t.assets)
    for (const a of assets) {
      const color = a.cut_off ? "#000" : a.exposed ? "#f97316" : "#334155";
      f.points.push({ lat: a.lat, lon: a.lon, radius: a.type === "shelter" ? 5 : 4,
        style: { color, fill: a.cut_off ? "#111" : ASSET_COLOR[a.type] ?? "#fff", weight: a.exposed ? 2.5 : 1.2, dash: a.exposed ? "2 2" : undefined },
        tooltip: `${a.name}${a.capacity ? ` · cap ${a.capacity}` : ""}${a.hazards.length ? ` · exposed: ${a.hazards.join(", ")}` : ""}${a.cut_off ? " · CUT OFF" : ""}` });
    }
  if (t.villages)
    for (const v of villages)
      f.points.push({ lat: v.lat, lon: v.lon, id: v.village_code,
        radius: 5 + Math.min(6, Math.log10(v.population / 500) * 3) + (v.village_code === selected ? 3 : 0),
        style: { color: v.village_code === selected ? "#000" : "#fff", fill: BAND_COLOR[v.risk_band], weight: v.village_code === selected ? 3 : 1.5 },
        tooltip: `${v.name} · Risk ${v.risk_score} (${v.risk_band}) · pop ${v.population.toLocaleString("en-IN")}` });
  const lf = s.scenario.forecast_landfall;
  f.points.push({ lat: lf.lat, lon: lf.lon, radius: 7, style: { color: "#c026d3", fill: "#f0abfc", weight: 3 }, tooltip: "Forecast landfall" });
  return f;
}
