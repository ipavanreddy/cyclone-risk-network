// Shapes returned by the TatRaksha API (services/api). Only fields the dashboards use are typed.

export type Integration = { name: string; mode: "real" | "demo"; env_vars: string[]; demo_fallback: string; runtime_error: string | null };
export type Status = { demo_mode: boolean; sample_data: boolean; force_demo_mode: boolean; integrations: Integration[] };

export type ReplayStep = { step: string; hours_before_landfall: number; issued_at: string; scenario_id: string };
export type Replay = {
  replay_id: string; code: string; cyclone_name: string; state: string; state_name: string; district: string;
  landfall_time: string; languages: string[]; steps: ReplayStep[];
};

export type TrackPoint = { time: string; lat: number; lon: number; max_wind_kmh: number; central_pressure_hpa: number | null; category: string | null };

export type KeyNumbers = {
  people_high_risk: number; villages_high_risk: number; people_in_surge_zone: number; substations_exposed: number;
  hospitals_exposed: number; shelters_exposed: number; shelters_cut_off: number; villages_without_reachable_shelter: number;
  roads_cut: number; evacuation_demand: number; reachable_shelter_capacity: number;
};

export type Provenance = { model_name: string; model_version: string; prompt_version: string; generated_at: string };

export type Grid = { lat_max: number; lon_min: number; cell_deg: number; rows: number; cols: number;
  bbox: { lat_min: number; lat_max: number; lon_min: number; lon_max: number } };

export type RoadLine = { edge_id: string; road: string; kind: string; cut: boolean; coords: [number, number][] };

export type ScenarioSummary = {
  scenario: {
    scenario_id: string; cyclone_name: string; state: string; state_name: string; district: string; step: string;
    forecast_issued_at: string; bulletin_no: string; track_verified: boolean; stage: string;
    hours_to_forecast_landfall: number; issuing_authority: string; languages: string[];
    forecast_landfall: { time: string; lat: number; lon: number; max_wind_kmh: number; central_pressure_hpa: number | null };
    track_verification: { verified_by: string; verified_at: string } | null;
  };
  bulletin: {
    text: string; mode: string; provenance: Provenance; requires_human_review: boolean;
    cross_check: { method: string; discrepancies: string[] };
    parse: { cyclone_name: string; issued_at: string; bulletin_no: string | null; track: TrackPoint[];
      expected_landfall: { area: string; time: string }; official_surge_text: string | null; confidence: number };
  };
  track: { points: TrackPoint[]; cone: [number, number][]; members: { k: number; line: [number, number][] }[];
    cone_radius_at_landfall_km: number };
  surge: { label: string; model_name: string; model_version: string; peak_surge_expected_m: number; peak_surge_high_m: number;
    inundated_km2_expected: number; inundated_km2_high: number; assumptions: string[];
    segments: { segment_id: string; lat: number; lon: number; surge_expected_m: number; surge_high_m: number }[] };
  flood: { label: string; model_name: string; model_version: string; rain_source: string; max_rain_72h_mm: number; assumptions: string[] };
  wind: { model: string; max_kmh: number; high_wind_threshold_kmh: number };
  key_numbers: KeyNumbers;
  freshness: { source: string; timestamp: string; note: string; is_sample: boolean; newer_available?: boolean }[];
  risk_model: { weights: Record<string, number>; doc: string };
  network: { roads_cut: string[]; cut_off_shelters: string[]; rule: string; roads: RoadLine[] };
  grid: Grid;
};

export type Hazards = { grid: Grid; layers: Record<string, (number | null)[]>; labels: { surge: string; flood: string } };

export type Village = {
  village_code: string; name: string; block: string; population: number; vulnerability_index: number; lat: number; lon: number;
  surge_depth_expected_m: number; surge_depth_high_m: number; flood_likelihood: number; max_wind_kmh: number; rain_72h_mm: number;
  gale_arrival_hours_before_landfall: number | null; shelter_reachable: boolean; nearest_reachable_shelter: string | null;
  shelter_distance_km: number | null; risk_score: number; risk_band: string; contributions: Record<string, number>;
  factors: Record<string, number>; priority_rank: number;
};

export type Asset = {
  asset_id: string; type: string; name: string; capacity: number | null; lat: number; lon: number; hazards: string[];
  exposed: boolean; safe?: boolean; cut_off?: boolean; assigned_evacuees?: number; over_capacity?: boolean;
};

export type Sitrep = Provenance & {
  report_id: string; scenario_id: string; headline: string; confidence: string; key_numbers: KeyNumbers; mode: string;
  actions: { role: string; action: string; deadline_hours_before_landfall: number; evidence: string[] }[];
  priority_villages: { village_code: string; name: string; risk_score: number; reason: string }[];
  shelters_attention: { asset_id: string; name: string; issue: string; recommendation: string }[];
  uncertainties: string[]; advisory_drafts: { audience: string; language: string; stage: string; text: string }[];
  inputs: { hazard_map_png: string; bulletin_no: string; multimodal: boolean };
  validation: { numbers_grounded: boolean; corrections: string[] };
};

export type Advisory = {
  advisory_id: string; scenario_id: string; state: string; district: string; stage: string; audience: string;
  language: string; language_name: string; village_code: string; area: { name: string }; risk_score: number; risk_band: string;
  headline: string; fields: Record<string, string>; text: string; draft_mode: string; review_note: string; notes: string[];
  cap_xml: string | null; status: "draft" | "approved" | "sent"; approved_by: string | null; approved_at: string | null;
  sent_at: string | null; created_at: string; model_name: string; model_version: string; prompt_version: string;
};

export type DispatchEntry = { log_id: string; advisory_id: string; channel: string; simulated: boolean; status: string;
  provider: string; at: string; by: string; note?: string; language: string; state: string };

export const BAND_COLOR: Record<string, string> = {
  "Very High": "#8c001e", High: "#e63c1e", Moderate: "#f5aa28", Low: "#3c9650",
};

export const STAGE_LABEL: Record<string, string> = {
  watch: "T-72h Watch", warning: "T-48h Warning", evacuation_order: "T-24h Evacuation Order", final_warning: "T-6h Final Warning",
};

export function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false }) + " IST";
}

export function fmtNum(n: number): string {
  return n.toLocaleString("en-IN");
}
