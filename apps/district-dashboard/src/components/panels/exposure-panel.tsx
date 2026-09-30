"use client";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BAND_COLOR, type Asset, type ScenarioSummary, type Village } from "@/lib/types";

const FACTOR_COLOR: Record<string, string> = {
  surge: "#1d4ed8", flood: "#15803d", wind: "#7e22ce", population: "#0f766e", vulnerability: "#b45309",
};

export function RiskBar({ v }: { v: Village }) {
  return (
    <div className="flex h-2.5 w-full overflow-hidden rounded bg-muted" title={Object.entries(v.contributions).map(([k, x]) => `${k} ${x}`).join(" · ")}>
      {Object.entries(v.contributions).map(([k, x]) => (
        <div key={k} style={{ width: `${x}%`, background: FACTOR_COLOR[k] }} />
      ))}
    </div>
  );
}

export function VillageDetail({ v, assets }: { v: Village; assets: Asset[] }) {
  const shelter = assets.find((a) => a.asset_id === v.nearest_reachable_shelter);
  return (
    <div className="space-y-2 rounded-lg border p-3">
      <div className="flex items-baseline justify-between">
        <p className="font-medium">{v.name} <span className="text-xs text-muted-foreground">({v.block} block · {v.village_code})</span></p>
        <p className="text-2xl font-semibold" style={{ color: BAND_COLOR[v.risk_band] }}>{v.risk_score}<span className="text-sm">/100 {v.risk_band}</span></p>
      </div>
      <RiskBar v={v} />
      <div className="grid grid-cols-5 gap-1 text-[11px]">
        {Object.entries(v.contributions).map(([k, x]) => (
          <div key={k}><span className="inline-block size-2 rounded-sm" style={{ background: FACTOR_COLOR[k] }} /> {k} <b>{x}</b></div>
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Surge {v.surge_depth_expected_m} m (high {v.surge_depth_high_m} m) · flood likelihood {v.flood_likelihood} · rain {v.rain_72h_mm} mm ·
        wind {v.max_wind_kmh} km/h{v.gale_arrival_hours_before_landfall != null && ` · gales from T-${v.gale_arrival_hours_before_landfall}h`} ·
        pop {v.population.toLocaleString("en-IN")} (sample) · vulnerability {v.vulnerability_index}
      </p>
      <p className="text-xs">
        {v.shelter_reachable
          ? <>Nearest reachable safe shelter: <b>{shelter?.name ?? v.nearest_reachable_shelter}</b> ({v.shelter_distance_km} km by road)</>
          : <span className="text-destructive">No safe shelter reachable by road within 30 km</span>}
      </p>
    </div>
  );
}

export function VillagesPanel({ villages, assets, selected, onSelect }: { villages: Village[]; assets: Asset[]; selected: string | null; onSelect: (c: string) => void }) {
  const sel = villages.find((v) => v.village_code === selected);
  return (
    <div className="space-y-3">
      {sel && <VillageDetail v={sel} assets={assets} />}
      <p className="text-xs text-muted-foreground">
        Village Risk = Surge 30 · Rainfall flood 25 · Wind 15 · Population 15 · Vulnerability 15 (transparent weighted model). Click a row or map circle.
      </p>
      <Table>
        <TableHeader>
          <TableRow><TableHead>#</TableHead><TableHead>Village</TableHead><TableHead>Risk</TableHead><TableHead className="w-28">Breakdown</TableHead><TableHead>Shelter</TableHead></TableRow>
        </TableHeader>
        <TableBody>
          {villages.map((v) => (
            <TableRow key={v.village_code} onClick={() => onSelect(v.village_code)}
              className={`cursor-pointer ${v.village_code === selected ? "bg-muted" : ""}`}>
              <TableCell>{v.priority_rank}</TableCell>
              <TableCell>{v.name}<div className="text-[10px] text-muted-foreground">{v.block}</div></TableCell>
              <TableCell><span className="font-semibold" style={{ color: BAND_COLOR[v.risk_band] }}>{v.risk_score}</span> <span className="text-[10px]">{v.risk_band}</span></TableCell>
              <TableCell><RiskBar v={v} /></TableCell>
              <TableCell>{v.shelter_reachable ? `${v.shelter_distance_km} km` : <Badge variant="destructive">none</Badge>}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function AssetsPanel({ s, assets }: { s: ScenarioSummary; assets: Asset[] }) {
  const groups = ["shelter", "substation", "hospital"];
  return (
    <div className="space-y-4">
      <div className="rounded-lg border p-3 text-xs">
        <p className="font-medium">Road cut-off analysis</p>
        <p className="text-muted-foreground">{s.network.rule}</p>
        <p className="mt-1">Roads cut: {s.network.roads_cut.length ? s.network.roads_cut.join(", ") : "none"}</p>
      </div>
      {groups.map((g) => (
        <div key={g}>
          <p className="mb-1 font-medium capitalize">{g}s <span className="text-xs text-muted-foreground">(sample locations)</span></p>
          <Table>
            <TableBody>
              {assets.filter((a) => a.type === g).map((a) => (
                <TableRow key={a.asset_id}>
                  <TableCell className="text-xs">{a.name}</TableCell>
                  <TableCell className="text-xs">{a.capacity ?? ""}</TableCell>
                  <TableCell className="space-x-1 text-right">
                    {a.hazards.map((h) => <Badge key={h} variant="outline" className="border-orange-400">{h}</Badge>)}
                    {a.cut_off && <Badge variant="destructive">cut off</Badge>}
                    {a.over_capacity && <Badge variant="destructive">over capacity ({a.assigned_evacuees})</Badge>}
                    {g === "shelter" && !a.cut_off && a.safe && <Badge className="bg-emerald-600 text-white">safe</Badge>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ))}
    </div>
  );
}
