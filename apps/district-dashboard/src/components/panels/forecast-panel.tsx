"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiPost } from "@/lib/api";
import { fmtTime, type ScenarioSummary } from "@/lib/types";

export function ForecastPanel({ s, officer, onChanged }: { s: ScenarioSummary; officer: string; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const b = s.bulletin;
  const sc = s.scenario;

  async function verify() {
    setBusy(true);
    setErr(null);
    try {
      await apiPost(`/api/scenarios/${sc.scenario_id}/track/verify`, { verified_by: officer, role: "District Disaster Management Officer" });
      onChanged();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="font-medium">Bulletin {b.parse.bulletin_no ?? sc.bulletin_no}</h3>
          <Badge variant={b.mode === "gemini" ? "default" : "outline"}>
            {b.mode === "gemini" ? `Parsed by ${b.provenance.model_name}` : "Demo parser (Gemini not configured)"}
          </Badge>
          <Badge variant="outline">prompt {b.provenance.prompt_version}</Badge>
          <Badge variant="outline">confidence {Math.round(b.parse.confidence * 100)}%</Badge>
        </div>
        <p className="text-muted-foreground">
          Issued {fmtTime(b.parse.issued_at)} · Expected landfall {b.parse.expected_landfall.area},{" "}
          {b.parse.expected_landfall.time.includes("T") ? fmtTime(b.parse.expected_landfall.time) : b.parse.expected_landfall.time}
        </p>
        {b.cross_check.discrepancies.length > 0 && (
          <div className="rounded border border-amber-400 bg-amber-50 p-2 text-xs text-amber-900">
            Cross-check vs {b.cross_check.method}: {b.cross_check.discrepancies.join("; ")}
          </div>
        )}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Time (IST)</TableHead><TableHead>Lat/Lon</TableHead><TableHead>Wind km/h</TableHead>
              <TableHead>hPa</TableHead><TableHead>Cat.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {b.parse.track.map((p) => (
              <TableRow key={p.time}>
                <TableCell>{fmtTime(p.time).replace(" IST", "")}</TableCell>
                <TableCell>{p.lat.toFixed(1)}°N {p.lon.toFixed(1)}°E</TableCell>
                <TableCell>{p.max_wind_kmh}</TableCell>
                <TableCell>{p.central_pressure_hpa ?? "–"}</TableCell>
                <TableCell>{p.category}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="flex flex-wrap items-center gap-2">
          {sc.track_verified ? (
            <Badge className="bg-emerald-600 text-white">
              Track verified by {sc.track_verification?.verified_by}
            </Badge>
          ) : (
            <>
              <Badge variant="destructive">Track not yet verified</Badge>
              <Button size="sm" onClick={verify} disabled={busy}>Verify extracted track as {officer}</Button>
            </>
          )}
        </div>
        {err && <p className="text-xs text-destructive">{err}</p>}
      </section>

      <section className="grid gap-2 rounded-lg border p-3">
        <p className="font-medium">Hazard models</p>
        <p>
          <Badge className="mr-2 bg-blue-700 text-white">{s.surge.label}</Badge>
          Peak surge {s.surge.peak_surge_expected_m} m expected / {s.surge.peak_surge_high_m} m high case ·
          inundation {s.surge.inundated_km2_expected}–{s.surge.inundated_km2_high} km²
        </p>
        <p className="text-xs">
          <span className="font-medium">Official guidance (bulletin): </span>
          {b.parse.official_surge_text ?? "not stated"}
        </p>
        <p className="text-xs text-muted-foreground">
          Track uncertainty ±{s.track.cone_radius_at_landfall_km} km at landfall · {s.wind.model} · max wind {Math.round(s.wind.max_kmh)} km/h
        </p>
        <p className="text-xs">
          <Badge variant="outline" className="mr-2">{s.flood.label}</Badge>
          Max 72 h rain {Math.round(s.flood.max_rain_72h_mm)} mm · {s.flood.rain_source}
        </p>
        <details className="text-xs text-muted-foreground">
          <summary className="cursor-pointer">Model assumptions</summary>
          <ul className="list-disc pl-5">
            {[...s.surge.assumptions, ...s.flood.assumptions].map((a) => <li key={a}>{a}</li>)}
          </ul>
        </details>
      </section>

      <section>
        <p className="mb-1 font-medium">Data freshness</p>
        <ul className="space-y-1 text-xs">
          {s.freshness.map((f) => (
            <li key={f.source}>
              <span className="font-medium">{f.source}</span> · {fmtTime(f.timestamp)} · {f.note}
              {f.is_sample && <Badge variant="outline" className="ml-1">sample</Badge>}
              {f.newer_available && <Badge variant="outline" className="ml-1">newer bulletin in replay</Badge>}
            </li>
          ))}
        </ul>
      </section>

      <details>
        <summary className="cursor-pointer text-sm font-medium">Bulletin text</summary>
        <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded bg-muted p-2 text-[11px]">{b.text}</pre>
      </details>
    </div>
  );
}
