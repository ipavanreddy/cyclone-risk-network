"""Canonical disaster-risk data model (PRD §21, §31). State adapters map state data into these."""
from pydantic import BaseModel


class DatasetMeta(BaseModel):
    source: str
    reference_timestamp: str
    dataset_version: str
    geographic_scope: str
    is_sample: bool = True
    is_synthetic: bool = False


class Village(BaseModel):
    village_code: str  # LGD code in production; SAMPLE-* codes in the replay datasets
    name: str
    block: str
    district: str
    state: str
    population: int
    vulnerability_index: float
    coastal_fishing: bool = False
    lat: float
    lon: float


class Asset(BaseModel):
    asset_id: str
    type: str  # shelter / substation / hospital / road / school
    name: str
    capacity: int | None = None
    criticality: str = "medium"
    near: str | None = None
    lat: float
    lon: float


class StateConfig(BaseModel):
    state: str
    state_name: str
    country: str
    districts: list[str]
    default_district: str
    replays: list[str]
    languages: list[str]
    primary_language: str
    admin_units: dict[str, str]
    issuing_authority: str
    cap_sender: str
    alert_gateway: str
    forecast_source: str
    risk_weights: dict[str, float]
    village_field_map: dict[str, str] = {}
    metadata: DatasetMeta
