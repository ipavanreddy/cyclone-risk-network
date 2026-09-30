"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { API_URL, apiPost } from "@/lib/api";
import { fmtNum, fmtTime, type Sitrep } from "@/lib/types";

const KN_LABEL: Record<string, string> = {
  people_high_risk: "People in High/Very High villages", villages_high_risk: "High-risk villages",
  people_in_surge_zone: "People in surge zone", substations_exposed: "Substations exposed", hospitals_exposed: "Hospitals exposed",
  shelters_exposed: "Shelters exposed", shelters_cut_off: "Shelters cut off", villages_without_reachable_shelter: "Villages without reachable shelter",
  roads_cut: "Arterial roads cut", evacuation_demand: "Evacuation demand (people)", reachable_shelter_capacity: "Reachable safe shelter capacity",
};

export function SitrepPanel({ scenarioId, sitrep, officer, onGenerated }: {
  scenarioId: string; sitrep: Sitrep | null; officer: string; onGenerated: (s: Sitrep) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    setErr(null);
    try {
      onGenerated(await apiPost<Sitrep>(`/api/scenarios/${scenarioId}/sitrep`, { requested_by: officer }));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Button onClick={generate} disabled={busy}>{busy ? "Generating…" : sitrep ? "Re-generate situation report" : "Generate situation report"}</Button>
        <span className="text-xs text-muted-foreground">Inputs: hazard map image + bulletin + exposure tables</span>
      </div>
      {err && <p className="text-xs text-destructive">{err}</p>}
      {!sitrep && <p className="text-muted-foreground">No situation report for this bulletin yet.</p>}
      {sitrep && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1.5">
            <Badge variant={sitrep.mode === "gemini" ? "default" : "outline"} className={sitrep.mode === "gemini" ? "" : "border-amber-500"}>
              {sitrep.mode === "gemini" ? sitrep.model_name : "Demo template (Gemini not configured)"}
            </Badge>
            <Badge variant="outline">model {sitrep.model_version}</Badge>
            <Badge variant="outline">prompt {sitrep.prompt_version}</Badge>
            <Badge variant="outline">confidence {sitrep.confidence}</Badge>
            <Badge variant="outline">{fmtTime(sitrep.generated_at)}</Badge>
            <Badge className="bg-emerald-600 text-white">numbers grounded in data</Badge>
          </div>
          <p className="text-base font-medium">{sitrep.headline}</p>
          {sitrep.validation.corrections.length > 0 && (
            <div className="rounded border border-amber-400 bg-amber-50 p-2 text-xs text-amber-900">
              Validation corrected AI output: {sitrep.validation.corrections.join("; ")}
            </div>
          )}
          <div className="grid grid-cols-2 gap-1.5 text-xs md:grid-cols-3">
            {Object.entries(sitrep.key_numbers).map(([k, v]) => (
              <div key={k} className="rounded border p-1.5"><div className="text-muted-foreground">{KN_LABEL[k] ?? k}</div><div className="text-sm font-semibold">{fmtNum(v)}</div></div>
            ))}
          </div>
          <div>
            <p className="mb-1 font-medium">Actions by role</p>
            <ul className="space-y-1.5">
              {sitrep.actions.map((a, i) => (
                <li key={i} className="rounded border p-2">
                  <div className="flex justify-between gap-2"><b>{a.role}</b><Badge variant="outline">by T-{a.deadline_hours_before_landfall}h</Badge></div>
                  <p>{a.action}</p>
                  <p className="text-[11px] text-muted-foreground">Evidence: {a.evidence.join(" · ")}</p>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-1 font-medium">Villages to prioritise for evacuation</p>
            <ol className="list-decimal pl-5 text-xs">
              {sitrep.priority_villages.map((v) => <li key={v.village_code}><b>{v.name}</b> – risk {v.risk_score} ({v.reason})</li>)}
            </ol>
          </div>
          {sitrep.shelters_attention.length > 0 && (
            <div>
              <p className="mb-1 font-medium">Shelters needing alternatives or pre-stocking</p>
              <ul className="list-disc pl-5 text-xs">
                {sitrep.shelters_attention.map((s) => <li key={s.asset_id}><b>{s.name}</b>: {s.issue} → {s.recommendation}</li>)}
              </ul>
            </div>
          )}
          <div>
            <p className="mb-1 font-medium">Uncertainties</p>
            <ul className="list-disc pl-5 text-xs">{sitrep.uncertainties.map((u) => <li key={u}>{u}</li>)}</ul>
          </div>
          <details>
            <summary className="cursor-pointer text-xs font-medium">Hazard map image sent to the model</summary>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`${API_URL}${sitrep.inputs.hazard_map_png}`} alt="Hazard map image used as multimodal input" className="mt-2 w-full rounded border" />
          </details>
          <p className="text-[11px] text-muted-foreground">AI interpretation for officer review. Actions and advisories require human approval.</p>
        </div>
      )}
    </div>
  );
}
