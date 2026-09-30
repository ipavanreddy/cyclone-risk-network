"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DemoBadge } from "@/components/demo-badge";
import { HazardMap } from "@/components/hazard-map";
import { apiGet, apiPost } from "@/lib/api";
import { buildFeatures, DEFAULT_TOGGLES } from "@/lib/map-features";
import {
  BAND_COLOR, STAGE_LABEL, fmtNum, fmtTime,
  type Advisory, type Asset, type DispatchEntry, type Hazards, type KeyNumbers, type Replay, type ScenarioSummary, type Village,
} from "@/lib/types";

type Block = { block: string; villages: number; population: number; people_high_risk: number; max_risk: number; no_shelter: number };
type DistrictRow = { replay_id: string; scenario_id: string; district: string; cyclone_name: string; stage: string;
  hours_to_forecast_landfall: number; key_numbers: KeyNumbers; blocks: Block[]; advisories: Record<string, number> };
type StateCfg = { state: string; state_name: string; languages: string[]; issuing_authority: string; alert_gateway: string;
  admin_units: Record<string, string>; village_field_map: Record<string, string>; risk_weights: Record<string, number> };
type Analytics = { state: StateCfg; districts: DistrictRow[] };
type Estimate = { policy_id: string; zone: string; trigger_definition: string; trigger_probability: number;
  expected_payout_crore: number; high_payout_crore: number; label: string };
type Verification = { policy_id: string; observed_max_wind_kmh: number; trigger_met: boolean; source: string };
type Validation = { method: string; confusion: Record<string, number>; hit_rate: number | null; false_alarm_ratio: number | null;
  villages: { village_code: string; name: string; predicted_flooded: boolean; observed_flooded: boolean | null }[] };
type AuditRow = { event: string; actor: string; role: string; at: string; details: Record<string, unknown> };

export function StateDashboard() {
  const [replays, setReplays] = useState<Replay[]>([]);
  const [stateId, setStateId] = useState("OD");
  const [stepIdx, setStepIdx] = useState(2);
  const [overview, setOverview] = useState<Record<string, Analytics>>({});
  const [summary, setSummary] = useState<ScenarioSummary | null>(null);
  const [hazards, setHazards] = useState<Hazards | null>(null);
  const [villages, setVillages] = useState<Village[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [dispatchLog, setDispatchLog] = useState<DispatchEntry[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [estimates, setEstimates] = useState<Estimate[]>([]);
  const [verified, setVerified] = useState<Record<string, Verification>>({});
  const [validation, setValidation] = useState<Validation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const replay = replays.find((r) => r.state === stateId);
  const step = replay?.steps[Math.min(stepIdx, (replay?.steps.length ?? 1) - 1)];
  const sid = step?.scenario_id;

  useEffect(() => {
    apiGet<Replay[]>("/api/replays").then(setReplays).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!replays.length || !step) return;
    const states = Array.from(new Set(replays.map((r) => r.state)));
    Promise.all(states.map((st) => apiGet<Analytics>(`/api/states/${st}/analytics?step=${step.step}`)))
      .then((rows) => setOverview(Object.fromEntries(rows.map((r) => [r.state.state, r]))))
      .catch((e) => setError(String(e)));
  }, [replays, step, tick]);

  useEffect(() => {
    if (!sid) return;
    let cancelled = false;
    Promise.all([
      apiGet<ScenarioSummary>(`/api/scenarios/${sid}`),
      apiGet<Hazards>(`/api/scenarios/${sid}/hazards?layer=surge_expected&layer=surge_high&layer=flood_likelihood&layer=water`),
      apiGet<Village[]>(`/api/scenarios/${sid}/villages`),
      apiGet<{ assets: Asset[] }>(`/api/scenarios/${sid}/exposure`),
      apiPost<{ estimates: Estimate[] }>(`/api/scenarios/${sid}/parametric`, {}),
      apiGet<Validation>(`/api/scenarios/${sid}/validation`),
    ])
      .then(([s, h, v, ex, p, val]) => {
        if (cancelled) return;
        setSummary(s); setHazards(h); setVillages(v); setAssets(ex.assets); setEstimates(p.estimates); setValidation(val);
        setError(null);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [sid]);

  useEffect(() => {
    Promise.all([
      apiGet<Advisory[]>(`/api/advisories?state=${stateId}`),
      apiGet<DispatchEntry[]>(`/api/dispatch-log?state=${stateId}`),
      apiGet<AuditRow[]>("/api/audit-log"),
    ]).then(([a, d, au]) => { setAdvisories(a); setDispatchLog(d); setAudit(au); }).catch((e) => setError(String(e)));
  }, [stateId, tick]);

  const refresh = useCallback(() => setTick((n) => n + 1), []);
  const current = summary && summary.scenario.scenario_id === sid ? summary : null;
  const features = useMemo(
    () => (current ? buildFeatures(current, hazards, villages, assets, { ...DEFAULT_TOGGLES, roads: false }, null) : null),
    [current, hazards, villages, assets],
  );
  const cfg = overview[stateId]?.state;
  const sampleVillage = villages[0];

  return (
    <main className="mx-auto flex w-full max-w-[1500px] flex-col gap-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">TatRaksha</h1>
            <p className="text-xs text-muted-foreground">Bay of Bengal cyclone anticipatory action · State Emergency Operations Centre</p>
          </div>
          <Badge variant="secondary">State EOC Officer</Badge>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex overflow-hidden rounded-lg border text-xs">
            {replays.map((r) => (
              <button key={r.state} onClick={() => setStateId(r.state)}
                className={`px-3 py-1.5 ${r.state === stateId ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}>
                {r.state_name}
              </button>
            ))}
          </div>
          <Button size="sm" variant="outline" onClick={refresh}>Refresh logs</Button>
          <DemoBadge />
        </div>
      </header>

      {replay && (
        <Card size="sm">
          <CardContent className="flex flex-wrap items-center gap-4 text-xs">
            <span className="font-medium">Replay clock</span>
            <input type="range" min={0} max={replay.steps.length - 1} value={Math.min(stepIdx, replay.steps.length - 1)}
              onChange={(e) => setStepIdx(Number(e.target.value))} className="w-60 accent-primary" aria-label="Replay time step" />
            {replay.steps.map((st, i) => (
              <button key={st.step} onClick={() => setStepIdx(i)} className={i === stepIdx ? "font-semibold underline" : "text-muted-foreground"}>
                T-{st.hours_before_landfall}h
              </button>
            ))}
            {current && <span>{current.scenario.cyclone_name} · bulletin {fmtTime(current.scenario.forecast_issued_at)} · landfall in ~{Math.round(current.scenario.hours_to_forecast_landfall)} h</span>}
          </CardContent>
        </Card>
      )}
      {error && <p className="rounded border border-destructive p-2 text-sm text-destructive">{error}</p>}

      <section className="grid gap-3 md:grid-cols-2">
        {Object.values(overview).map((a) => a.districts.map((d) => (
          <Card key={d.scenario_id} size="sm" className={a.state.state === stateId ? "ring-2 ring-primary" : ""}>
            <CardHeader><CardTitle>{a.state.state_name} · {d.district} · {d.cyclone_name}</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-4 gap-2 text-xs">
              <div><div className="text-muted-foreground">Stage</div><Badge className="bg-red-700 text-white">{STAGE_LABEL[d.stage]}</Badge></div>
              <div><div className="text-muted-foreground">Landfall in</div><b>{Math.round(d.hours_to_forecast_landfall)} h</b></div>
              <div><div className="text-muted-foreground">People high risk</div><b>{fmtNum(d.key_numbers.people_high_risk)}</b></div>
              <div><div className="text-muted-foreground">Shelters cut off</div><b>{d.key_numbers.shelters_cut_off}</b></div>
              <div><div className="text-muted-foreground">Substations exp.</div><b>{d.key_numbers.substations_exposed}</b></div>
              <div><div className="text-muted-foreground">Hospitals exp.</div><b>{d.key_numbers.hospitals_exposed}</b></div>
              <div><div className="text-muted-foreground">Roads cut</div><b>{d.key_numbers.roads_cut}</b></div>
              <div><div className="text-muted-foreground">Advisories</div>{d.advisories.draft}d · {d.advisories.approved}a · {d.advisories.sent}s</div>
            </CardContent>
          </Card>
        )))}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card size="sm">
          <CardHeader><CardTitle>District / block comparison {cfg && `– ${cfg.state_name}`}</CardTitle></CardHeader>
          <CardContent>
            {overview[stateId]?.districts.map((d) => (
              <Table key={d.scenario_id}>
                <TableHeader><TableRow><TableHead>{d.district}: {cfg?.admin_units.level_3}</TableHead><TableHead>Villages</TableHead><TableHead>Population</TableHead><TableHead>In high-risk villages</TableHead><TableHead>Max risk</TableHead><TableHead>No shelter</TableHead></TableRow></TableHeader>
                <TableBody>
                  {d.blocks.map((b) => (
                    <TableRow key={b.block}>
                      <TableCell>{b.block}</TableCell><TableCell>{b.villages}</TableCell><TableCell>{fmtNum(b.population)}</TableCell>
                      <TableCell>{fmtNum(b.people_high_risk)}</TableCell>
                      <TableCell><span className="font-semibold" style={{ color: BAND_COLOR[b.max_risk >= 75 ? "Very High" : b.max_risk >= 55 ? "High" : b.max_risk >= 35 ? "Moderate" : "Low"] }}>{b.max_risk}</span></TableCell>
                      <TableCell>{b.no_shelter || ""}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ))}
            <p className="mt-2 text-[11px] text-muted-foreground">Sample villages and populations; one district per state in this MVP.</p>
          </CardContent>
        </Card>
        <div className="space-y-2">
          <HazardMap features={features} height={420} />
          {current && <Badge className="bg-blue-700 text-white">{current.surge.label}</Badge>}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card size="sm">
          <CardHeader><CardTitle>Parametric trigger estimates (sample policies)</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-xs">
            <Badge variant="outline" className="border-amber-500">Planning estimate for liquidity preparation – not a payout decision</Badge>
            <Table>
              <TableHeader><TableRow><TableHead>Zone</TableHead><TableHead>Trigger</TableHead><TableHead>P(trigger)</TableHead><TableHead>Expected (₹ cr)</TableHead><TableHead>High-end (₹ cr)</TableHead><TableHead>Post-event</TableHead></TableRow></TableHeader>
              <TableBody>
                {estimates.map((e) => (
                  <TableRow key={e.policy_id}>
                    <TableCell className="whitespace-normal">{e.zone}</TableCell>
                    <TableCell className="whitespace-normal">{e.trigger_definition}</TableCell>
                    <TableCell className="font-semibold">{Math.round(e.trigger_probability * 100)}%</TableCell>
                    <TableCell>{e.expected_payout_crore}</TableCell>
                    <TableCell>{e.high_payout_crore}</TableCell>
                    <TableCell>
                      {verified[e.policy_id] ? (
                        <span>{verified[e.policy_id].trigger_met ? "Trigger met" : "Not met"} ({verified[e.policy_id].observed_max_wind_kmh} km/h)</span>
                      ) : (
                        <Button size="xs" variant="outline" onClick={() => apiPost<Verification>(`/api/parametric/${e.policy_id}/verify`, {})
                          .then((v) => setVerified((m) => ({ ...m, [e.policy_id]: v })))}>Verify</Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <p className="text-muted-foreground">Probability = share of track-set members meeting the wind trigger. Verification uses the replay&apos;s reconstructed track (sample).</p>
          </CardContent>
        </Card>
        <Card size="sm">
          <CardHeader><CardTitle>Validation: predicted vs observed flooding (replay)</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-xs">
            {validation && (
              <>
                <p className="text-muted-foreground">{validation.method}. Observed flags are a labelled synthetic sample; real mode uses Sentinel-1 SAR flood extents.</p>
                <div className="flex gap-3">
                  <Badge variant="outline">hits {validation.confusion.tp}</Badge><Badge variant="outline">misses {validation.confusion.fn}</Badge>
                  <Badge variant="outline">false alarms {validation.confusion.fp}</Badge><Badge variant="outline">correct negatives {validation.confusion.tn}</Badge>
                  <Badge>hit rate {validation.hit_rate ?? "–"}</Badge><Badge variant="secondary">FAR {validation.false_alarm_ratio ?? "–"}</Badge>
                </div>
              </>
            )}
            {cfg && sampleVillage && (
              <details>
                <summary className="cursor-pointer font-medium">Interoperability: common data structure for {cfg.state_name}</summary>
                <p className="mt-1 text-muted-foreground">State field names are mapped to the canonical schema by the state adapter
                  {Object.keys(cfg.village_field_map).length ? ` (${Object.entries(cfg.village_field_map).map(([k, v]) => `${v}→${k}`).join(", ")})` : " (Odisha data already canonical)"}.
                  Languages: {cfg.languages.join(", ")} · Alert gateway: {cfg.alert_gateway}</p>
                <pre className="mt-1 max-h-56 overflow-auto rounded bg-muted p-2 text-[10px]">{JSON.stringify({
                  state: current?.scenario.state, district: current?.scenario.district, scenario_id: current?.scenario.scenario_id,
                  cyclone: { name: current?.scenario.cyclone_name, forecast_issued: current?.scenario.forecast_issued_at,
                    landfall_eta_hours: current?.scenario.hours_to_forecast_landfall, max_wind_kmh: current?.scenario.forecast_landfall.max_wind_kmh },
                  village: { lgd_code: sampleVillage.village_code, population: sampleVillage.population, surge_depth_m: sampleVillage.surge_depth_expected_m,
                    flood_likelihood: sampleVillage.flood_likelihood, risk_score: sampleVillage.risk_score, nearest_reachable_shelter: sampleVillage.nearest_reachable_shelter },
                  assets_exposed: assets.filter((a) => a.exposed).slice(0, 3).map((a) => ({ asset_id: a.asset_id, type: a.type, hazard: a.hazards[0] })),
                }, null, 2)}</pre>
              </details>
            )}
          </CardContent>
        </Card>
      </div>

      <Card size="sm">
        <CardHeader><CardTitle>Advisory log – {cfg?.state_name}</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-xs">
          {advisories.length === 0 && <p className="text-muted-foreground">No advisories yet. District officers draft and approve advisories in the District dashboard.</p>}
          {advisories.length > 0 && (
            <Table>
              <TableHeader><TableRow><TableHead>Advisory</TableHead><TableHead>Area</TableHead><TableHead>Lang</TableHead><TableHead>Stage</TableHead><TableHead>Status</TableHead><TableHead>Approved by</TableHead><TableHead>Sent</TableHead><TableHead>Model / prompt</TableHead></TableRow></TableHeader>
              <TableBody>
                {[...advisories].reverse().map((a) => (
                  <TableRow key={a.advisory_id}>
                    <TableCell className="text-[10px]">{a.advisory_id}</TableCell><TableCell>{a.area.name}</TableCell><TableCell>{a.language}</TableCell>
                    <TableCell>{STAGE_LABEL[a.stage]}</TableCell><TableCell><Badge variant="outline">{a.status}</Badge></TableCell>
                    <TableCell>{a.approved_by ?? "–"}</TableCell><TableCell>{a.sent_at ? fmtTime(a.sent_at) : "–"}</TableCell>
                    <TableCell className="text-[10px]">{a.model_name} / {a.prompt_version}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <p className="mb-1 font-medium">Dispatch log</p>
              <ul className="max-h-48 space-y-0.5 overflow-auto">
                {dispatchLog.slice().reverse().map((d) => (
                  <li key={d.log_id}>{fmtTime(d.at)} · {d.channel} · <b>{d.status}</b> · {d.provider}{d.simulated && " (simulated)"} · {d.advisory_id} · by {d.by}</li>
                ))}
                {!dispatchLog.length && <li className="text-muted-foreground">No dispatches.</li>}
              </ul>
            </div>
            <div>
              <p className="mb-1 font-medium">Audit trail</p>
              <ul className="max-h-48 space-y-0.5 overflow-auto">
                {audit.slice().reverse().slice(0, 50).map((a, i) => (
                  <li key={i}>{fmtTime(a.at)} · {a.event} · {a.actor} ({a.role}) · {String(a.details.id ?? "")}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
      <p className="text-[11px] text-muted-foreground">All replay data are labelled samples. Map data © OpenStreetMap contributors.</p>
    </main>
  );
}
