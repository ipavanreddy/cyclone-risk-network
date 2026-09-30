"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiGetText, apiPost } from "@/lib/api";
import { STAGE_LABEL, fmtTime, type Advisory, type DispatchEntry, type Village } from "@/lib/types";

const LANG_NAME: Record<string, string> = { en: "English", or: "Odia", bn: "Bengali" };
const SPEECH_LANG: Record<string, string> = { en: "en-IN", or: "or-IN", bn: "bn-IN" };
const CHANNELS = ["sms", "messaging", "voice", "alert_feed"];
const STATUS_COLOR: Record<string, string> = { draft: "bg-slate-500", approved: "bg-blue-600", sent: "bg-emerald-600" };

async function speak(a: Advisory, setNote: (s: string) => void) {
  const res = await apiPost<{ mode: string; audio_url: string | null; engine: string }>("/api/text-to-speech", { text: a.text, language: a.language });
  if (res.audio_url) {
    setNote(`Playing ${res.engine} audio`);
    await new Audio(res.audio_url).play();
    return;
  }
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(a.text);
    u.lang = SPEECH_LANG[a.language] ?? "en-IN";
    const voice = window.speechSynthesis.getVoices().find((v) => v.lang.startsWith(a.language));
    if (voice) u.voice = voice;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    setNote(`Demo: browser speech preview (${u.lang}${voice ? "" : ", no matching voice installed – may read in default voice"})`);
  } else {
    setNote("No speech synthesis available in this browser");
  }
}

function AdvisoryCard({ a, officer, onChange }: { a: Advisory; officer: string; onChange: () => void }) {
  const [reviewed, setReviewed] = useState(false);
  const [cap, setCap] = useState<string | null>(null);
  const [channels, setChannels] = useState<string[]>(["sms", "voice", "alert_feed"]);
  const [log, setLog] = useState<DispatchEntry[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run(fn: () => Promise<void>) {
    setErr(null);
    try {
      await fn();
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="space-y-2 rounded-lg border p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge className={`${STATUS_COLOR[a.status]} text-white`}>{a.status}</Badge>
        <Badge variant="outline">{LANG_NAME[a.language]}</Badge>
        <Badge variant="outline">{STAGE_LABEL[a.stage] ?? a.stage}</Badge>
        <Badge variant="outline">{a.audience}</Badge>
        <Badge variant="outline">{a.draft_mode === "gemini" ? a.model_name : a.draft_mode === "template" ? "approved template" : a.draft_mode}</Badge>
        <span className="text-[10px] text-muted-foreground">{a.advisory_id}</span>
      </div>
      <p className="text-sm font-medium">{a.headline}</p>
      <p className="whitespace-pre-wrap rounded bg-muted p-2 text-sm" lang={a.language}>{a.text}</p>
      <details className="text-xs">
        <summary className="cursor-pointer">Mandatory fields</summary>
        <dl className="grid grid-cols-[6rem_1fr] gap-x-2">
          {Object.entries(a.fields).map(([k, v]) => (
            <div key={k} className="contents"><dt className="font-medium">{k}</dt><dd>{v}</dd></div>
          ))}
        </dl>
      </details>
      <p className="text-[11px] text-muted-foreground">{a.review_note} · prompt {a.prompt_version}</p>
      {a.notes.map((n) => <p key={n} className="text-[11px] text-amber-700">{n}</p>)}
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" onClick={() => run(() => speak(a, setNote))}>▶ Audio preview</Button>
        {a.status === "draft" && (
          <>
            {a.language !== "en" && (
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} />
                Translation reviewed
              </label>
            )}
            <Button size="sm" disabled={a.language !== "en" && !reviewed}
              onClick={() => run(async () => {
                await apiPost(`/api/advisories/${a.advisory_id}/approve`, { approved_by: officer, role: "District Disaster Management Officer", translation_reviewed: reviewed });
                onChange();
              })}>
              Approve as {officer}
            </Button>
          </>
        )}
        {a.status !== "draft" && (
          <Button size="sm" variant="outline" onClick={() => run(async () => setCap(cap ? null : await apiGetText(`/api/advisories/${a.advisory_id}/cap`)))}>
            {cap ? "Hide" : "View"} CAP 1.2
          </Button>
        )}
      </div>
      {a.approved_by && <p className="text-[11px]">Approved by {a.approved_by} at {fmtTime(a.approved_at!)}{a.sent_at && ` · sent ${fmtTime(a.sent_at)}`}</p>}
      {a.status === "approved" && (
        <div className="flex flex-wrap items-center gap-2 rounded border p-2 text-xs">
          {CHANNELS.map((c) => (
            <label key={c} className="flex items-center gap-1">
              <input type="checkbox" checked={channels.includes(c)}
                onChange={(e) => setChannels(e.target.checked ? [...channels, c] : channels.filter((x) => x !== c))} />
              {c}
            </label>
          ))}
          <Button size="sm" disabled={!channels.length}
            onClick={() => run(async () => {
              const res = await apiPost<{ dispatch: DispatchEntry[] }>(`/api/advisories/${a.advisory_id}/dispatch`, { channels, dispatched_by: officer, role: "District Disaster Management Officer" });
              setLog(res.dispatch);
              onChange();
            })}>
            Dispatch (sandbox)
          </Button>
        </div>
      )}
      {log.length > 0 && (
        <ul className="text-[11px]">
          {log.map((l) => (
            <li key={l.log_id}>{l.channel}: <b>{l.status}</b> via {l.provider}{l.simulated && " (simulated – no sandbox credentials)"}</li>
          ))}
        </ul>
      )}
      {note && <p className="text-[11px] text-muted-foreground">{note}</p>}
      {cap && <pre className="max-h-64 overflow-auto rounded bg-muted p-2 text-[10px]">{cap}</pre>}
      {err && <p className="text-xs text-destructive">{err}</p>}
    </div>
  );
}

export function AdvisoryPanel({ scenarioId, stage, languages, villages, selected, onSelect, advisories, officer, onChange }: {
  scenarioId: string; stage: string; languages: string[]; villages: Village[]; selected: string | null;
  onSelect: (c: string) => void; advisories: Advisory[]; officer: string; onChange: () => void;
}) {
  const langs = Array.from(new Set(["en", ...languages]));
  const [language, setLanguage] = useState(langs[langs.length - 1]);
  const [audience, setAudience] = useState("public");
  const [stageSel, setStageSel] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const village = selected ?? villages[0]?.village_code;

  async function draft() {
    setBusy(true);
    setErr(null);
    try {
      await apiPost("/api/advisories/draft", { scenario_id: scenarioId, village_code: village, language, audience,
        stage: stageSel || null, requested_by: officer });
      onChange();
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  }

  const sel = "h-8 rounded-md border bg-background px-2 text-sm";
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 rounded-lg border p-3 text-xs">
        <label className="col-span-2 flex flex-col gap-1">Area (village)
          <select className={sel} value={village} onChange={(e) => onSelect(e.target.value)}>
            {villages.map((v) => <option key={v.village_code} value={v.village_code}>{v.name} – risk {v.risk_score} ({v.risk_band})</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">Language
          <select className={sel} value={language} onChange={(e) => setLanguage(e.target.value)}>
            {langs.map((l) => <option key={l} value={l}>{LANG_NAME[l] ?? l}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">Audience
          <select className={sel} value={audience} onChange={(e) => setAudience(e.target.value)}>
            <option value="public">Public</option><option value="fishers">Fishers</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">Stage
          <select className={sel} value={stageSel} onChange={(e) => setStageSel(e.target.value)}>
            <option value="">Current ({STAGE_LABEL[stage]})</option>
            {Object.entries(STAGE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
        <div className="flex items-end"><Button onClick={draft} disabled={busy || !village}>{busy ? "Drafting…" : "Draft advisory"}</Button></div>
        {err && <p className="col-span-2 text-destructive">{err}</p>}
      </div>
      {advisories.length === 0 && <p className="text-muted-foreground">No advisories for this bulletin yet.</p>}
      {[...advisories].reverse().map((a) => <AdvisoryCard key={a.advisory_id} a={a} officer={officer} onChange={onChange} />)}
    </div>
  );
}
