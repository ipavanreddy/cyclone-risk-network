"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { apiGet } from "@/lib/api";
import type { Status } from "@/lib/types";

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";

/** Visible "Demo mode / sample data" indicator with per-integration detail. */
export function DemoBadge() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiGet<Status>("/api/status").then(setStatus).catch(() => setError(true));
  }, []);

  if (error) return <Badge variant="destructive">API unreachable</Badge>;
  if (!status) return <Badge variant="outline">Checking integrations…</Badge>;
  const items = status.integrations.map((i) =>
    i.name === "maps" ? { ...i, mode: (MAPS_KEY ? "real" : "demo") as "real" | "demo" } : i,
  );
  const demo = items.filter((i) => i.mode === "demo");
  const live = items.length - demo.length;
  return (
    <details className="relative">
      <summary className="flex cursor-pointer list-none items-center gap-1.5">
        {live > 0 && <Badge className="bg-emerald-700 text-white hover:bg-emerald-700">{live} integrations live</Badge>}
        {demo.length > 0 && (
          <Badge className="bg-amber-500 text-black hover:bg-amber-500">Demo mode · {demo.length} fallbacks</Badge>
        )}
        {status.sample_data && <Badge className="bg-sky-700 text-white">Sample data (replay)</Badge>}
      </summary>
      <div className="absolute right-0 z-[1000] mt-2 w-[26rem] rounded-lg border bg-background p-3 text-xs shadow-lg">
        <p className="mb-2 font-medium">Integrations (live = configured and verified by a real call)</p>
        <ul className="space-y-1.5">
          {items.map((i) => (
            <li key={i.name} className="flex gap-2">
              <Badge variant={i.mode === "real" ? "default" : "outline"} className="shrink-0">
                {i.mode === "real" ? "live" : "demo"}
              </Badge>
              <span>
                <span className="font-medium">{i.name}</span>
                {i.mode === "demo" && <> – {i.demo_fallback}. Set {i.env_vars.join(", ")}.</>}
                {i.runtime_error && <span className="text-destructive"> Error: {i.runtime_error}</span>}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-muted-foreground">
          Replay datasets (tracks, bulletins, villages, shelters, assets, roads) are labelled sample data.
        </p>
      </div>
    </details>
  );
}
