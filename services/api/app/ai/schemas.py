"""Structured Gemini output schemas (PRD §33). Exported to ai/schemas/*.schema.json by export_schemas.py."""
from typing import Literal

from pydantic import BaseModel, Field


# ---- Bulletin parsing (prompt: ai/prompts/bulletin_parse_v1.md) --------------------------------
class TrackPoint(BaseModel):
    time: str = Field(description="ISO 8601 with +05:30 offset, exactly as given in the bulletin table")
    lat: float
    lon: float
    max_wind_kmh: int = Field(description="Upper value of the maximum sustained wind range")
    central_pressure_hpa: int | None = None
    category: str | None = None


class ExpectedLandfall(BaseModel):
    area: str
    time: str = Field(description="ISO 8601 if a clock time can be derived, else the bulletin wording")


class BulletinParse(BaseModel):
    cyclone_name: str
    bulletin_no: str | None = None
    issued_at: str
    track: list[TrackPoint]
    expected_landfall: ExpectedLandfall
    official_surge_text: str | None = Field(default=None, description="Storm surge guidance sentence, verbatim")
    confidence: float = Field(ge=0, le=1)
    requires_human_review: bool = True


# ---- Situation report (prompt: ai/prompts/sitrep_v1.md) ----------------------------------------
class KeyNumbers(BaseModel):
    people_high_risk: int
    villages_high_risk: int
    people_in_surge_zone: int
    substations_exposed: int
    hospitals_exposed: int
    shelters_exposed: int
    shelters_cut_off: int
    villages_without_reachable_shelter: int
    roads_cut: int
    evacuation_demand: int
    reachable_shelter_capacity: int


class RoleAction(BaseModel):
    role: str
    action: str
    deadline_hours_before_landfall: int
    evidence: list[str]


class PriorityVillage(BaseModel):
    village_code: str
    name: str
    risk_score: int
    reason: str


class ShelterNote(BaseModel):
    asset_id: str
    name: str
    issue: str
    recommendation: str


class AdvisoryDraftBrief(BaseModel):
    audience: str
    language: str
    stage: str
    text: str


class SituationReport(BaseModel):
    headline: str
    confidence: Literal["low", "medium", "high"]
    key_numbers: KeyNumbers
    actions: list[RoleAction]
    priority_villages: list[PriorityVillage]
    shelters_attention: list[ShelterNote]
    uncertainties: list[str]
    advisory_drafts: list[AdvisoryDraftBrief]


# ---- Advisory drafting (prompt: ai/prompts/advisory_v1.md) -------------------------------------
class AdvisoryFields(BaseModel):
    what: str = Field(description="Hazard")
    where: str = Field(description="Area")
    when: str = Field(description="Timing")
    action: str = Field(description="What to do")
    shelter: str = Field(description="Where to go")
    authority: str = Field(description="Issuing authority")


class AdvisoryDraft(BaseModel):
    headline: str
    fields: AdvisoryFields
    text: str = Field(description="Short, clear public message containing every mandatory field")


ALL_SCHEMAS: dict[str, type[BaseModel]] = {
    "bulletin_parse_v1": BulletinParse,
    "sitrep_v1": SituationReport,
    "advisory_v1": AdvisoryDraft,
}
