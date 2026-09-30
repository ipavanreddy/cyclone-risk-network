"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DemoBadge } from "@/components/demo-badge";
import { HazardMap } from "@/components/hazard-map";
import { AdvisoryPanel } from "@/components/panels/advisory-panel";
import { AssetsPanel, VillagesPanel } from "@/components/panels/exposure-panel";
import { ForecastPanel } from "@/components/panels/forecast-panel";
import { SitrepPanel } from "@/components/panels/sitrep-panel";
import { apiGet, apiPost } from "@/lib/api";
import { buildFeatures, DEFAULT_TOGGLES, type LayerToggles } from "@/lib/map-features";
import {
  STAGE_LABEL, fmtNum, fmtTime,
  type Advisory, type Asset, type Hazards, type Replay, type ScenarioSummary, type Sitrep, type Village,
} from "@/lib/types";

type Bundle = { summary: ScenarioSummary; hazards: Hazards; villages: Village[]; assets: Asset[]; sitrep: Sitrep | null;
  advisories: Advisory[]; tileUrl: string | null };

const TOGGLE_LABEL: Record<keyof LayerToggles, string> = {
  surge: "Surge (expected)", surgeHigh: "Surge (high case)", flood: "Rain-flood likelihood", wind: "Wind swath",
  cone: "Track cone", members: "Track set", villages: "Village risk", assets: "Assets & shelters", roads: "Roads / cut-offs",
};

async function loadBundle(sid: string): Promise<Bundle> {
  const [summary, hazards, villages, exposure, advisories, tiles] = await Promise.all([
    apiGet<ScenarioSummary>(`/api/scenarios/${sid}`),
    apiGet<Hazards>(`/api/scenarios/${sid}/hazards?layer=surge_expected&layer=surge_high&layer=flood_likelihood&layer=wind_max&layer=water`),
    apiGet<Village[]>(`/api/scenarios/${sid}/villages?sort=risk`),
    apiGet<{ assets: Asset[] }>(`/api/scenarios/${sid}/exposure`),
    apiGet<Advisory[]>(`/api/advisories?scenario=${sid}`),
    apiGet<{ tiles: { url_format: string } | null }>(`/api/scenarios/${sid}/hazards/ee-tiles`).catch(() => ({ tiles: null })),
  ]);
  const sitrep = await apiGet<Sitrep>(`/api/scenarios/${sid}/sitrep`).catch(() => null);
  return { summary, hazards, villages, assets: exposure.assets, sitrep, advisories, tileUrl: tiles.tiles?.url_format ?? null };
}

function param(name: string): string | null {
  return typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get(name);
}

function Kpi({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="rounded-lg border bg-card px-3 py-2">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className={`text-lg font-semibold ${tone ?? ""}`}>{typeof value === "number" ? fmtNum(value) : value}</div>
    </div>
  );
}

export function DistrictDashboard() {
  const [replays, setReplays] = useState<Replay[]>([]);
  // deep links for demos: ?replay=amphan-2020&step=2&tab=sitrep
  const [replayId, setReplayId] = useState(() => param("replay") ?? "fani-2019");
  const [stepIdx, setStepIdx] = useState(() => Number(param("step") ?? 0));
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toggles, setToggles] = useState<LayerToggles>(DEFAULT_TOGGLES);
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<string>(() => param("tab") ?? "forecast");
  const [officer, setOfficer] = useState("A. Das (DDMO, demo)");
  const [reload, setReload] = useState(0);

  const replay = replays.find((r) => r.replay_id === replayId);
  const step = replay?.steps[stepIdx];
  const scenarioId = step?.scenario_id;

  useEffect(() => {
    apiGet<Replay[]>("/api/replays").then(setReplays).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!scenarioId || !replay) return;
    let cancelled = false;
    // POST /api/scenarios registers the replay scenario (idempotent), then load everything for it
    apiPost("/api/scenarios", { mode: "replay", replay_id: replay.replay_id, step: step!.step })
      .then(() => loadBundle(scenarioId))
      .then((b) => {
        if (cancelled) return;
        setBundle(b);
        setError(null);
      })
      .catch((e) => !cancelled && setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [scenarioId, replay, step, reload]);

  const refresh = useCallback(() => setReload((n) => n + 1), []);
  const current = bundle && bundle.summary.scenario.scenario_id === scenarioId ? bundle : null;
  const features = useMemo(
    () => (current ? buildFeatures(current.summary, current.hazards, current.villages, current.assets, toggles, selected, current.tileUrl) : null),
    [current, toggles, selected],
  );

  const s = current?.summary;
  const kn = s?.key_numbers;
  const advCounts = current ? (["draft", "approved", "sent"] as const).map((st) => current.advisories.filter((a) => a.status === st).length).join(" / ") : "";

  return (
    <main className="mx-auto flex w-full max-w-[1500px] flex-col gap-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">TatRaksha</h1>
            <p className="text-xs text-muted-foreground">Cyclone anticipatory action & early warning</p>
          </div>
          <Badge variant="secondary">District Disaster Management Officer</Badge>
          {s && <Badge variant="outline">{s.scenario.state_name} · {s.scenario.district}</Badge>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex overflow-hidden rounded-lg border text-xs">
            {replays.map((r) => (
              <button key={r.replay_id} onClick={() => { setReplayId(r.replay_id); setStepIdx(0); setSelected(null); }}
                className={`px-3 py-1.5 ${r.replay_id === replayId ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}>
                {r.state_name} · {r.cyclone_name} {r.landfall_time.slice(0, 4)}
              </button>
            ))}
          </div>
          <label className="flex items-center gap-1 text-xs">Officer<Input className="h-7 w-44 text-xs" value={officer} onChange={(e) => setOfficer(e.target.value)} /></label>
          <DemoBadge />
        </div>
      </header>

      {replay && (
        <Card size="sm">
          <CardContent className="flex flex-wrap items-center gap-4">
            <div className="text-xs font-medium">Replay time slider</div>
            <input type="range" min={0} max={replay.steps.length - 1} value={stepIdx} onChange={(e) => setStepIdx(Number(e.target.value))}
              className="w-72 accent-primary" aria-label="Replay time step" />
            <div className="flex gap-3 text-xs">
              {replay.steps.map((st, i) => (
                <button key={st.step} onClick={() => setStepIdx(i)} className={i === stepIdx ? "font-semibold underline" : "text-muted-foreground"}>
                  T-{st.hours_before_landfall}h
                </button>
              ))}
            </div>
            {s && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Badge className="bg-red-700 text-white">{STAGE_LABEL[s.scenario.stage]}</Badge>
                <span>Bulletin {s.scenario.bulletin_no} issued {fmtTime(s.scenario.forecast_issued_at)}</span>
                <span>· Forecast landfall in <b>{Math.round(s.scenario.hours_to_forecast_landfall)} h</b> ({fmtTime(s.scenario.forecast_landfall.time)})</span>
                {!s.scenario.track_verified && <Badge variant="destructive">track unverified</Badge>}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {error && <p className="rounded border border-destructive p-2 text-sm text-destructive">{error}</p>}
      {!current && !error && <p className="text-muted-foreground">Loading scenario…</p>}

      {current && s && kn && (
        <>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4 lg:grid-cols-8">
            <Kpi label="People in high-risk villages" value={kn.people_high_risk} tone="text-red-700" />
            <Kpi label="High-risk villages" value={kn.villages_high_risk} />
            <Kpi label="People in surge zone" value={kn.people_in_surge_zone} />
            <Kpi label="Substations exposed" value={kn.substations_exposed} />
            <Kpi label="Hospitals exposed" value={kn.hospitals_exposed} />
            <Kpi label="Shelters exposed" value={kn.shelters_exposed} />
            <Kpi label="Shelters cut off" value={kn.shelters_cut_off} tone={kn.shelters_cut_off ? "text-red-700" : ""} />
            <Kpi label="Advisories draft / approved / sent" value={advCounts} />
          </div>

          <div className="grid gap-4 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
            <div className="space-y-2">
              <HazardMap features={features} onSelect={(id) => { setSelected(id); setTab("villages"); }} />
              <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
                {(Object.keys(TOGGLE_LABEL) as (keyof LayerToggles)[]).map((k) => (
                  <label key={k} className="flex items-center gap-1">
                    <input type="checkbox" checked={toggles[k]} onChange={(e) => setToggles({ ...toggles, [k]: e.target.checked })} />
                    {TOGGLE_LABEL[k]}
                  </label>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                <Badge className="bg-blue-700 text-white">{s.surge.label}</Badge>
                <span><span className="inline-block size-2.5 rounded-sm bg-[#1e3a8a]" /> surge depth</span>
                <span><span className="inline-block size-2.5 rounded-sm bg-[#93c5fd]" /> high-case only</span>
                <span><span className="inline-block size-2.5 rounded-sm bg-[#4d9c5a]" /> flood likelihood ≥ 0.35</span>
                <span>Villages: <span className="text-[#8c001e]">●</span> Very High <span className="text-[#e63c1e]">●</span> High <span className="text-[#f5aa28]">●</span> Moderate <span className="text-[#3c9650]">●</span> Low</span>
                <span>Shelters ○ safe · ● cut off · dashed orange = exposed · red dashed road = cut</span>
              </div>
            </div>

            <Tabs value={tab} onValueChange={(v) => setTab(String(v))}>
              <TabsList className="w-full">
                <TabsTrigger value="forecast">Forecast</TabsTrigger>
                <TabsTrigger value="villages">Village risk</TabsTrigger>
                <TabsTrigger value="assets">Assets</TabsTrigger>
                <TabsTrigger value="sitrep">Sitrep</TabsTrigger>
                <TabsTrigger value="advisories">Advisories</TabsTrigger>
              </TabsList>
              <div className="max-h-[640px] overflow-y-auto pr-1">
                <TabsContent value="forecast"><ForecastPanel s={s} officer={officer} onChanged={refresh} /></TabsContent>
                <TabsContent value="villages"><VillagesPanel villages={current.villages} assets={current.assets} selected={selected} onSelect={setSelected} /></TabsContent>
                <TabsContent value="assets"><AssetsPanel s={s} assets={current.assets} /></TabsContent>
                <TabsContent value="sitrep">
                  <SitrepPanel scenarioId={s.scenario.scenario_id} sitrep={current.sitrep} officer={officer}
                    onGenerated={(r) => setBundle({ ...current, sitrep: r })} />
                </TabsContent>
                <TabsContent value="advisories">
                  <AdvisoryPanel key={replayId} scenarioId={s.scenario.scenario_id} stage={s.scenario.stage} languages={s.scenario.languages}
                    villages={current.villages} selected={selected} onSelect={setSelected} advisories={current.advisories}
                    officer={officer} onChange={refresh} />
                </TabsContent>
              </div>
            </Tabs>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Official forecast/observed data → model estimates (surge, flood, exposure) → AI interpretation → recommendation. All replay data are
            labelled samples; every advisory requires approval by the District Disaster Management Officer. Map data © OpenStreetMap contributors.
          </p>
        </>
      )}
    </main>
  );
}
