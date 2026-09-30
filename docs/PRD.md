# AI-Powered Cyclone Anticipatory Action & Early-Warning Platform

## Product Requirements Document (PRD)

**Document Version:** 2.0 (aligned to the PRD 04 template)
**Working Name:** TatRaksha (तटरक्षा)
**Track:** 5: Predictive risk & vulnerability modelling for Bay of Bengal / coastal APAC cyclones
**Product Type:** AI-powered Disaster Risk Intelligence Platform / Interoperable Public Infrastructure
**Target Geography:** India's east coast (Bay of Bengal), extensible to coastal APAC
**Primary User:** District Disaster Management Officer
**Secondary User:** State Emergency Operations Centre (EOC) Officer
**Mandated Technology:** Google Earth Engine satellite feeds, real-time meteorological data, Gemini 3.7 Flash multimodal reasoning
**Primary Objective:** Turn an official cyclone forecast into a local impact forecast (surge flooding, rainfall flooding, exposed people and critical infrastructure) and send approved, multilingual early-warning advisories before landfall, on an interoperable foundation that works across states and countries.

---

# 1. Executive Summary

Cyclones in the Bay of Bengal regularly affect Odisha, West Bengal, Andhra Pradesh, Tamil Nadu and neighbouring countries. India has greatly improved cyclone forecasting and evacuation, but local authorities still need to answer, quickly and repeatedly as forecasts change:

- **Which villages** will flood from storm surge or heavy rain?
- **Which roads** will be cut, and **which shelters** will become unreachable?
- **Which substations, power lines and hospitals** are at risk?
- **What should each department do**, and **when**?
- **What should we tell the public**, in their language?
- **Will insurance triggers be hit**, so money can be released early?

The information needed exists in satellite data, weather forecasts, official bulletins and infrastructure lists, but combining it takes time that authorities don't have.

The proposed solution is an **AI-powered cyclone anticipatory action platform** that:

1. **Ingests the official forecast** and real-time weather data.
2. **Simulates storm surge** (screening level) and maps likely coastal flooding.
3. **Predicts rainfall flooding pathways** using a model trained on past events.
4. **Maps exposure** of people and critical infrastructure (power grid, arterial roads, hospitals, shelters).
5. Uses **Gemini 3.7 Flash multimodal reasoning** to produce a situation report and role-specific actions.
6. **Drafts and dispatches early-warning advisories** in local languages, in a standard alert format, after human approval.
7. **Estimates parametric insurance trigger probabilities**, so money can be ready before landfall.
8. Provides **a common data and API architecture** so states and neighbouring countries can join.

The hackathon MVP will focus on a single, polished end-to-end journey:

> **Cyclone Forecast → Surge + Rainfall Hazard → Exposure → Gemini Situation Report → Advisory Approval → Multilingual Dispatch**

The prototype will also show that the same architecture supports several states. It uses a **replay of a past cyclone** as the main demo, because a live cyclone may not occur during the hackathon.

---

# 2. Problem Statement

## 2.1 Core Problem

Extreme weather events in the Bay of Bengal and coastal APAC require rapid anticipatory action. Many decisions are still made late, or at a coarse level, because local impact information isn't ready in time.

Authorities often rely on:

- Official track and intensity bulletins without local impact detail
- Static hazard maps
- Manual compilation of shelter, road and asset lists
- Manually written advisories in several languages
- Post-landfall damage assessment to trigger financial support

This creates several risks:

- Evacuation that is late or poorly targeted
- Shelters that become unreachable once roads flood
- Power infrastructure damaged without pre-emptive protection
- Hospitals not prepared for patient transfer
- Delayed warnings in local languages
- Relief funding that arrives only after the damage
- Livelihood losses, especially for fishers and coastal farmers

Shifting from post-landfall recovery to **pre-landfall action** (evacuation planning, infrastructure hardening and parametric insurance liquidity) saves lives and livelihoods.

---

# 3. Challenge

The challenge is to build an **AI-powered predictive risk and vulnerability modelling platform** that uses:

- **Google Earth Engine** satellite feeds
- **Real-time meteorological data**
- **Gemini 3.7 Flash's multimodal reasoning**

The solution should:

- **Simulate cyclone storm surges**.
- **Predict local rainfall damage pathways**.
- **Map exposure for critical infrastructure** (power grids, arterial roads, medical shelters).
- **Automate early-warning advisory dispatches** for local municipal and disaster management authorities.
- Use AI meaningfully rather than as a generic chatbot.
- Scale across states and coastal APAC.

---

# 4. Product Vision

> **Build a cyclone impact intelligence layer so that 72 hours before landfall, every district knows which villages will flood, which roads will be cut and which assets to protect, and has an approved, multilingual warning ready to send.**

Long term, the platform should function as shared public infrastructure, where:

- States and countries keep their own asset, shelter and population data.
- A common data contract defines how forecasts, hazards, assets, exposure and advisories are represented.
- Shared APIs expose impact intelligence and advisories.
- Alerts use international standards (Common Alerting Protocol).
- New states and countries are onboarded through data adapters rather than a rebuilt application.

---

# 5. Product Goals

## 5.1 Primary Goals

1. Ingest an official cyclone forecast and real-time weather data.
2. Simulate storm surge and map likely coastal flooding (screening level).
3. Predict rainfall flooding likelihood using a model trained on past events.
4. Map exposure of population, power infrastructure, arterial roads, hospitals and shelters.
5. Identify shelters that become unreachable when roads flood.
6. Use Gemini 3.7 Flash multimodal reasoning to produce a situation report and role-specific actions.
7. Generate multilingual, standards-based advisories with human approval and dispatch.
8. Estimate parametric insurance trigger probability.
9. Demonstrate a common data model across at least two state configurations.
10. Deliver a working, deployed end-to-end prototype, including a replay of a past cyclone.

## 5.2 Secondary Goals

- Validate predictions against observed satellite flood extents from past cyclones.
- Re-draft advisories automatically as forecasts update.
- Establish reusable disaster risk APIs.
- Support post-landfall rapid damage assessment (roadmap).

---

# 6. Non-Goals for the Hackathon MVP

The prototype will not replace official forecasting or emergency command systems.

Out of scope for the MVP:

- Replacing official cyclone track and intensity forecasts. The platform **consumes** them.
- Operational-grade hydrodynamic storm-surge modelling. The MVP uses a **screening model**.
- Sending real public alerts. The demo uses sandbox channels.
- Full evacuation logistics (vehicles, staff rostering)
- Relief distribution and inventory management
- Insurance policy issuance, pricing or claims payment
- Post-disaster reconstruction planning
- Earthquake, tsunami or other hazards

---

# 7. Target Users

The MVP contains only two application roles.

## 7.1 Primary User: District Disaster Management Officer

The District Disaster Management Officer represents the District Disaster Management Authority, working with the District Collector and municipal bodies.

### Characteristics

- Must make fast decisions under uncertainty
- Coordinates many departments (revenue, police, power, health, fisheries, municipal)
- Needs clear, location-specific, prioritised information
- Must communicate with the public in local languages
- Accountable for decisions

### Primary Questions

The platform should help answer:

- Which villages and wards face surge or rainfall flooding?
- How many people are at risk?
- Which shelters are safe and reachable?
- Which substations, roads and hospitals are exposed?
- What should each department do, and by when?
- What should we tell the public now?

---

## 7.2 Secondary User: State Emergency Operations Centre Officer

The State EOC Officer represents the State Disaster Management Authority / state emergency operations centre, including state finance and risk-financing staff.

### Primary Needs

The State EOC Officer should be able to:

- View the state-wide impact picture across districts.
- Compare districts to prioritise response resources.
- Review advisories issued by districts.
- View parametric insurance trigger probabilities.
- Explore data through the common interoperability layer.

### MVP Scope

The State EOC experience is primarily read-focused:

- State dashboard
- District comparison
- Exposure summaries
- Advisory log
- Parametric insurance panel
- State configuration

Command-and-control workflows (resource deployment orders) are outside the MVP.

### Advisory Recipients (not app users)

Advisories are **delivered to** the public, fishers, power utilities, hospitals, municipal bodies and police. They receive messages but don't log into the MVP.

---

# 8. Core Product Experience

The product centres on one high-quality end-to-end journey:

```text
Official Cyclone Forecast (bulletin + weather data)
   ↓
Gemini Parses Bulletin → Structured Track
   ↓
Track Uncertainty + Wind Field
   ↓
Storm Surge Simulation → Coastal Flooding
   ↓
Rainfall Flooding Likelihood
   ↓
Exposure: People, Power, Roads, Hospitals, Shelters
   ↓
Village Risk Score + Shelter Reachability
   ↓
Gemini 3.7 Flash Situation Report + Role-specific Actions
   ↓
Advisory Drafts (multilingual, standard alert format)
   ↓
District Officer Reviews & Approves
   ↓
Dispatch (SMS / messaging / voice / alert feed – sandbox)
   ↓
Parametric Trigger Estimate for State
```

This journey is the primary demonstration for the hackathon.

---

# 9. Module 1: Cyclone Forecast Ingest

## Purpose

Bring the official forecast and real-time weather data into the platform in a structured form.

### Inputs

- Official cyclone bulletins (India Meteorological Department regional centre): track points, intensity, expected landfall
- Numerical weather forecast fields (wind, rainfall, pressure) via Earth Engine
- Near-real-time satellite rainfall estimates
- Tide levels

### Google AI Role

**Gemini** reads bulletin PDFs and text and extracts a structured track (time, position, intensity, pressure, wind radius). The extraction is shown to the officer for verification.

### Track Uncertainty

- Generate a set of plausible tracks around the official forecast using typical historical forecast errors.
- Compute a wind field for each track using a standard parametric wind model.

### Requirement

Every forecast input carries its issue time and source. When a new bulletin arrives, the downstream analysis is re-run.

---

# 10. Module 2: Hazard & Exposure Base Layers

## Purpose

Prepare the geospatial foundation using **Google Earth Engine**.

### Layers

- Elevation (digital elevation model)
- Near-shore bathymetry (seabed slope)
- Permanent water bodies
- Drainage and flow accumulation
- Land cover
- Historical flood extents from radar satellite imagery (past cyclones)
- Building footprints (Google Open Buildings)
- Population density

### Requirement

Base layers are prepared once per state and reused for every cyclone. Each carries its source and date.

---

# 11. Module 3: Storm Surge Simulation

## Purpose

Estimate how high sea water may rise along the coast and which areas it may flood.

### Approach (Screening Level)

```text
Surge height per coastal segment ≈ f(central pressure drop, maximum wind,
                                     storm size, forward speed, approach angle,
                                     near-shore seabed slope) + tide
```

- Coefficients are calibrated against published surge values from past Bay of Bengal cyclones.
- Inundation is mapped in Earth Engine: land below the surge height **and** connected to the sea, reduced with distance inland.
- Results are given as a range (expected / high) across the track set.

### Output

- Surge height by coastal segment
- Inundation area and depth bands
- Villages and assets inside the surge zone

### Safety Requirement

The interface must label this a **"Screening estimate – defer to official surge guidance"**. Official surge products can replace the screening model through the same interface when they are available.

---

# 12. Module 4: Rainfall Damage Pathways

## Purpose

Predict where heavy cyclone rainfall is likely to cause flooding and damage.

### Inputs

- Forecast rainfall (24 / 48 / 72 hours)
- Recent rainfall (how wet the ground already is)
- Terrain slope and height above nearest drainage
- Flow accumulation (where water collects)
- Land cover
- Distance to rivers
- Historical flood frequency

### MVP Technical Approach

- A **Vertex AI** model (e.g. gradient-boosted trees) predicting flood likelihood per grid cell.
- Trained on flood extents observed by radar satellite imagery after past cyclones.
- Pathways shown as flow direction from high-rainfall areas to low-lying settlements and roads.

### Output

- Flood-likelihood map (low / medium / high)
- Settlements, roads and assets in likely flood areas

---

# 13. Village Risk Score

The prototype should present an easy-to-understand risk score for each village or ward.

Example:

```text
Village Risk
86 / 100
Very High
```

### Factors

- Storm surge depth
- Rainfall flood likelihood
- Wind severity
- Population exposed
- Vulnerability (housing type, elderly/children share, shelter access)

### MVP Implementation

The score uses a **transparent weighted model**:

```text
Village Risk =
  Surge Hazard × 30%
+ Rainfall Flood Likelihood × 25%
+ Wind Severity × 15%
+ Population Exposure × 15%
+ Vulnerability × 15%
```

The weights are configurable and documented. Villages are ranked for evacuation priority.

### Future Evolution

The rule-based score can later be supplemented by a Vertex AI damage-prediction model trained on past cyclone impacts.

---

# 14. Module 5: Critical Infrastructure Exposure

## Purpose

Identify which critical assets are at risk so they can be protected or worked around.

### Asset Types (MVP)

- **Power**: substations, transmission / distribution lines
- **Roads**: arterial roads and highways
- **Health**: hospitals and community health centres
- **Shelters**: cyclone shelters and capacity
- Schools used as shelters (where listed)

### Analysis

- Assets inside surge, flood or high-wind zones
- **Road cut-off analysis**: remove flooded road segments from the road network and check which villages can still reach a safe shelter
- Shelter capacity compared with the population needing evacuation

### Example

```text
Exposure Summary – Puri District (T-72h)

People in high-risk zones: ~340,000
Substations exposed: 12
Hospitals exposed: 4
Shelters exposed: 38
Shelters likely cut off if NH-316 floods: 9
```

---

# 15. Module 6: Gemini 3.7 Flash Situation Reasoning

## Purpose

Turn maps, bulletins and exposure data into a clear situation report and prioritised actions, fast enough to re-run whenever the forecast updates.

### Inputs (Multimodal)

- Official bulletin (PDF / text)
- Hazard map images (surge, flood, wind)
- Satellite imagery (pre-event context)
- Structured exposure tables
- Shelter and asset lists

### Google AI Role

**Gemini 3.7 Flash** reasons across images, documents and tables together. It returns a **structured situation report** with role-specific actions. It uses tools to query exposure data rather than guessing numbers.

### Situation Report Output

1. Headline
2. Key numbers (from the data)
3. Actions by role and deadline (e.g. District Authority, Power Utility, Health, Municipal, Police, Fisheries)
4. Villages to prioritise for evacuation
5. Shelters needing alternatives or pre-stocking
6. Uncertainties
7. Advisory drafts

### Example Actions

```text
District Authority – by T-48h
Evacuate 57 villages (priority list attached); open 44 shelters;
arrange alternatives for 9 shelters likely to be cut off.

Power Utility – by T-6h
Prepare pre-emptive shutdown of 6 coastal feeders;
stage restoration crews at 3 depots outside the high-wind zone.

Health – by T-24h
Transfer dialysis and maternity patients from 2 exposed health centres.
```

---

# 16. Module 7: Early-Warning Advisory Dispatch

## Purpose

Get the right warning to the right people, in their language, on time.

### Flow

```text
Situation Report + Village Risk
        ↓
Advisory Drafts (per area × audience × language)
        ↓
District Officer Review & Approval
        ↓
Standard Alert Message (Common Alerting Protocol)
        ↓
Dispatch: SMS / messaging / voice call / alert feed (sandbox in MVP)
        ↓
Dispatch Log
```

### Advisory Content (mandatory fields)

- What (hazard)
- Where (area)
- When (timing)
- What to do (action)
- Where to go (shelter)
- Issuing authority

### Warning Stages

```text
T-72h Watch → T-48h Warning → T-24h Evacuation Order → T-6h Final Warning
```

Advisories are re-drafted when the forecast updates. Every dispatch needs human approval.

### Standard Format

Advisories are also produced as **CAP 1.2** (Common Alerting Protocol) messages. That is the international standard used by national alerting systems and public alert aggregators, so it slots into existing government alert gateways.

---

# 17. Module 8: Parametric Insurance Trigger Estimation

## Purpose

Help state finance departments and insurers prepare money **before** landfall.

### Approach

- Define insured zones and triggers, e.g.:
  - Maximum sustained wind ≥ a threshold within a set distance of the zone
  - Rainfall over 72 hours ≥ a threshold
- Use the set of plausible tracks to estimate:
  - **Probability that the trigger will be met**
  - **Expected payout** and a high-end estimate
- After landfall, verify the trigger against observed data and produce a verification report.

### Example

```text
Parametric Cover – Zone A (Coastal Fisher Households)

Trigger: Max wind ≥ 120 km/h within 50 km
Probability of trigger: 64%
Expected payout: ₹X crore (sample)
High-end estimate: ₹Y crore (sample)
```

### Safety Requirement

These are **estimates to support liquidity planning**, not payout decisions.

---

# 18. Module 9: Multilingual Support & Voice

## MVP Languages

The prototype should demonstrate at least:

- English
- Odia
- Bengali

The architecture should support additional languages (Telugu, Tamil and others), including cross-border languages (e.g. Bangla for Bangladesh, Burmese for Myanmar) through configuration only.

### Flow

```text
Structured Advisory
     ↓
Gemini Draft (English)
     ↓
Translation + Approved Templates
     ↓
Human Review
     ↓
Text + Text-to-Speech Audio
```

### Requirement

Life-safety wording uses **pre-approved templates** where possible, and translations are reviewed. At least one complete voice advisory should be demonstrated.

---

# 19. Module 10: Disaster Officer Dashboard & Cyclone Replay

## Purpose

Give officers one view of the forecast, hazards, exposure, actions and advisories, and let them replay past cyclones for training and validation.

### Dashboard Levels

```text
Region (Bay of Bengal)
 ↓
State
 ↓
District
 ↓
Block / Village / Ward
```

### Dashboard Metrics

- Forecast track and uncertainty
- Time to landfall
- People in high-risk zones
- Exposed substations, hospitals, shelters
- Cut-off shelters
- Advisories (draft / approved / sent)
- Parametric trigger probability (State EOC)

### Map View

- Track cone and wind swath
- Surge inundation
- Rainfall flood likelihood
- Village risk
- Critical assets
- Road cut-offs
- Time slider (T-72h → landfall)

### Cyclone Replay

- Replay a past cyclone (e.g. Fani 2019 in Odisha, Amphan 2020 in West Bengal) from T-72 hours.
- Compare predicted flooding with flooding actually observed by radar satellite imagery.

---

# 20. Module 11: Interoperability Layer

This is a core architectural requirement and a major differentiator of the solution.

## Objective

Provide a common data and service structure so different states, and neighbouring countries, can participate without separate applications.

### Core Principle

> **State-specific data, common interfaces.**

Each state or country may have:

- Different shelter and asset lists
- Different forecast sources
- Different languages
- Different administrative units
- Different alert gateways

But the platform exposes a standardised canonical representation.

---

# 21. Common Disaster Risk Data Model

Example:

```json
{
  "state": "OD",
  "district": "Puri",
  "scenario_id": "FANI-2019-T72",
  "cyclone": {
    "name": "Fani",
    "forecast_issued": "2019-04-30T12:00:00+05:30",
    "landfall_eta_hours": 72,
    "max_wind_kmh": 185
  },
  "village": {
    "lgd_code": "XXXXXX",
    "population": 4200,
    "surge_depth_m": 1.8,
    "flood_likelihood": 0.72,
    "risk_score": 86,
    "nearest_reachable_shelter": "SH-PURI-017"
  },
  "assets_exposed": [
    { "asset_id": "SS-PURI-03", "type": "substation", "hazard": "surge" }
  ],
  "advisory": {
    "stage": "warning",
    "languages": ["or", "en"],
    "status": "approved"
  }
}
```

The same structure should support examples such as:

```text
Odisha → Puri (surge-dominated)
West Bengal → South 24 Parganas / Sundarbans (surge + embankment breach)
Andhra Pradesh → Coastal delta (rainfall flooding)
```

The MVP does not need complete coastal coverage. It needs to prove that the architecture is state-agnostic.

---

# 22. Interoperability Principles

## 22.1 Common Interfaces

State (and country) services expose compatible APIs.

## 22.2 Canonical Schema

Core concepts have common definitions for:

- Cyclone Scenario
- Forecast Track
- Hazard Cell
- Village / Ward
- Asset
- Shelter
- Exposure
- Advisory
- Parametric Policy

## 22.3 State Data Adapters

A state-specific adapter transforms local shelter lists, asset registers and boundaries into the canonical schema.

```text
State Dataset
     ↓
State Adapter
     ↓
Canonical Disaster Risk Schema
     ↓
Shared Platform Services
```

## 22.4 Model Portability

Surge and flood models consume standardised features. Earth Engine base layers are global, so models transfer to new coasts with local calibration.

## 22.5 Open Standards

- **CAP 1.2**: Common Alerting Protocol for advisories
- **GeoJSON / Cloud-Optimised GeoTIFF**: exports for state GIS teams
- **LGD codes**: Indian administrative units, with configurable boundaries for other countries

## 22.6 API-First Design

External government and partner applications should eventually be able to consume:

- Hazard layers
- Exposure summaries
- Village risk
- Advisories
- Parametric trigger estimates

---

# 23. System Architecture

```text
                 DISTRICT OFFICER / STATE EOC OFFICER
                                │
                             Web App
                                │
                                ▼
                         Next.js Frontend
                                │
                                ▼
                            API Layer
                                │
   ┌──────────────┬─────────────┼──────────────┬───────────────┐
   ▼              ▼             ▼              ▼               ▼
Forecast      Hazard         Exposure       Situation       Advisory &
Ingest        Service        Service        Reasoning       Parametric
Service    (Surge + Flood)  (Assets, Roads) Service         Services
   │              │             │              │               │
   └──────────────┴──────┬──────┴──────────────┴───────────────┘
                         ▼
                Disaster Risk Data Layer
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
   BigQuery          Firebase         Cloud Storage
       │
  ┌────┴──────────────────────────┐
  ▼                               ▼
Public / Global Data          State Data
 ├── Forecast bulletins        ├── Odisha
 ├── Weather (GEE)             ├── West Bengal
 ├── Satellite (GEE)           ├── Andhra Pradesh
 └── Buildings / population    └── Other States / Countries
  └──────────────┬────────────────┘
                 ▼
            AI / ML Layer
                 │
     ┌───────────┼────────────┐
     ▼           ▼            ▼
 Gemini 3.7   Vertex AI    Earth Engine
 Flash        Flood Model  Processing
 Multimodal
     └───────────┼────────────┘
                 ▼
   Situation Report / Risk / Advisories
                 │
         ┌───────┴────────┐
         ▼                ▼
   Translation      Voice Services
         │                │
         └───────┬────────┘
                 ▼
     Approved Dispatch (CAP / SMS / Voice)
```

---

# 24. Recommended Technology Stack

## 24.1 Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- PWA capabilities
- Google Maps JavaScript API (+ deck.gl layers for hazard rasters and networks)

### Frontend Responsibilities

- Scenario selection (live / replay)
- Forecast and hazard maps with time slider
- Village risk and exposure views
- Situation report display
- Advisory composer, preview and approval
- Language switching and audio preview
- State EOC dashboard and parametric panel

---

# 25. Backend

## Recommended

**Google Cloud Run** (+ Cloud Scheduler / Pub/Sub for forecast update triggers)

Backend may be implemented using:

- FastAPI / Python for Earth Engine, modelling and AI services
- Node.js where application services benefit from it

### Responsibilities

- API routing
- Bulletin and weather ingestion
- Track uncertainty and wind field
- Earth Engine surge / flood processing
- Flood model serving
- Exposure and road cut-off analysis
- Gemini orchestration
- CAP message generation and sandbox dispatch
- Parametric calculations
- State adapters
- Authentication / authorisation

---

# 26. Google AI Technology Stack

## Gemini 3.7 Flash (Multimodal)

Use for:

- Reading bulletins (PDF / text) into a structured track
- Reasoning over hazard maps, imagery and exposure tables together
- Situation reports and role-specific action plans
- Advisory drafting
- Post-event image comparison (roadmap)

## Vertex AI

Use for:

- Rainfall flood-likelihood model
- Model training and serving
- Future damage-prediction models

## Google Earth Engine

Use for:

- Satellite and geospatial processing (see Section 27)

## Google AI Studio

Use for:

- Prompt experimentation
- Evaluating multimodal reasoning behaviour
- Initial prompt development

---

# 27. Geospatial Stack

## Google Earth Engine

- Elevation and bathymetry
- Weather forecast fields and satellite rainfall
- Radar satellite imagery for historical flood extents
- Optical satellite imagery for context
- Permanent water and drainage
- Building footprints (Open Buildings) and population
- Surge inundation and flood-likelihood processing
- Exposure statistics

## Google Maps Platform

- Map visualisation
- Road network context and routing (shelter reachability)
- Geographic context for advisories

---

# 28. Data Platform

## BigQuery

Primary analytical store for:

- Scenarios and forecast tracks
- Hazard grid results
- Villages, assets and shelters
- Exposure results
- Advisories and dispatch log
- Parametric policies and estimates
- Model features

## Firebase

Use for:

- Authentication
- Real-time updates as forecasts change
- Lightweight application state

## Cloud Storage

Use for:

- Bulletin files
- Map renders and imagery tiles
- Exported hazard layers
- Advisory audio

---

# 29. Public Data Sources

The architecture should be able to consume data from sources such as:

- **India Meteorological Department**: cyclone bulletins and best-track data
- **NOAA GFS** weather forecast (Earth Engine)
- **GPM IMERG** satellite rainfall (Earth Engine)
- **ERA5** historical weather (Earth Engine)
- **Copernicus DEM / SRTM** elevation, **GEBCO** bathymetry
- **Sentinel-1** radar and **Sentinel-2** optical imagery (Earth Engine)
- **JRC Global Surface Water**, **HydroSHEDS** drainage (Earth Engine)
- **Google Open Buildings**, **WorldPop / GHSL** population (Earth Engine)
- **OpenStreetMap**: roads, power infrastructure, hospitals (attributed)
- **State disaster management authority** shelter lists
- **INCOIS** ocean state information (where available)
- **ISRO / Bhuvan** thematic layers

Where live APIs are unavailable during the hackathon, use realistic sample or cached public data.

Every dataset must keep its source metadata and timestamps.

---

# 30. Data Architecture

```text
Bulletins + Weather        Earth Engine Layers       State Asset / Shelter Data
        │                          │                            │
        ▼                          ▼                            ▼
                         Data Ingestion
                                │
                                ▼
                    Validation / Normalisation
                                │
                                ▼
                    State Adapter (where needed)
                                │
                                ▼
                 Canonical Disaster Risk Schema
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
              BigQuery                  Feature Data
                  │                           │
                  └─────────────┬─────────────┘
                                ▼
           Surge / Flood / Exposure / Gemini Reasoning
                                │
                                ▼
            Situation Report / Advisories / Parametric
```

---

# 31. Core Data Entities

## Scenario

```text
scenario_id
cyclone_name
mode (live / replay)
forecast_issued_at
source
track
track_set_size
created_at
```

## Hazard Cell

```text
scenario_id
cell_id
surge_depth_expected
surge_depth_high
flood_likelihood
max_wind_kmh
arrival_hours_before_landfall
model_name
model_version
```

## Village

```text
lgd_code
name
district
state
population
vulnerability_index
geometry
```

## Asset

```text
asset_id
type (substation / line / road / hospital / shelter / school)
name
capacity
criticality
geometry
source
```

## Exposure

```text
scenario_id
village_code / asset_id
hazard_type
hazard_level
risk_score
shelter_reachable
nearest_reachable_shelter
```

## Situation Report

```text
report_id
scenario_id
headline
key_numbers
actions
uncertainties
generated_at
model_name
model_version
prompt_version
```

## Advisory

```text
advisory_id
scenario_id
stage
audience
area_geometry
language
text
cap_xml
audio_url
status (draft / approved / sent)
approved_by
sent_at
model_name
model_version
prompt_version
```

## Parametric Policy

```text
policy_id
zone_geometry
trigger_definition
trigger_probability
expected_payout
high_payout
verified
verified_at
```

---

# 32. AI Orchestration Architecture

AI services follow a predictable pipeline.

```text
New Bulletin / Forecast Update
      ↓
Gemini Bulletin Parsing → Structured Track
      ↓
Officer Verifies Track
      ↓
Track Set + Wind Field (deterministic)
      ↓
Surge Simulation + Earth Engine Inundation
      ↓
Vertex AI Flood Likelihood
      ↓
Exposure + Road Cut-off + Village Risk (deterministic)
      ↓
Gemini 3.7 Flash Multimodal Reasoning (maps + bulletin + tables, via tools)
      ↓
Structured JSON Output
      ↓
Validation (numbers grounded in data, mandatory advisory fields)
      ↓
Localisation (templates + translation)
      ↓
Human Approval
      ↓
Dispatch + Log
```

Physical and statistical models compute the hazards and numbers. Gemini reasons, prioritises and communicates. It never invents values.

---

# 33. Structured AI Output

AI services return structured outputs rather than free text.

## Bulletin Parsing

```json
{
  "cyclone_name": "Fani",
  "issued_at": "2019-04-30T12:00:00+05:30",
  "track": [
    { "time": "2019-05-01T00:00:00+05:30", "lat": 16.4, "lon": 85.9, "max_wind_kmh": 185, "central_pressure_hpa": 950 }
  ],
  "expected_landfall": { "area": "near Puri", "time": "2019-05-03 forenoon" },
  "confidence": 0.93,
  "requires_human_review": true
}
```

## Situation Report

```json
{
  "headline": "Extremely severe cyclone likely to cross near Puri in ~72h.",
  "confidence": "medium",
  "key_numbers": {
    "people_high_risk": 340000,
    "substations_exposed": 12,
    "hospitals_exposed": 4,
    "shelters_cut_off": 9
  },
  "actions": [
    {
      "role": "District Authority",
      "action": "Evacuate priority villages (list attached)",
      "deadline_hours_before_landfall": 48,
      "evidence": ["surge_depth > 1.5 m", "risk_score > 80"]
    }
  ],
  "uncertainties": ["Landfall position uncertainty ±40 km", "Screening surge model"],
  "advisory_drafts": [
    { "audience": "public", "language": "en", "stage": "warning", "text": "..." }
  ]
}
```

---

# 34. Prompt Architecture

Use specialised prompts for distinct capabilities.

## 34.1 Bulletin Parsing Prompt

### Inputs

- Bulletin PDF or text

### Requirements

- Extract track points, intensity, pressure and expected landfall.
- Never invent values that aren't in the bulletin.
- Return structured JSON for officer verification.

## 34.2 Situation Reasoning Prompt (Gemini 3.7 Flash)

### Inputs

- Hazard map images
- Bulletin
- Exposure tables (via tool calls)
- Shelter and asset lists
- Action templates by role

### Requirements

- Use only supplied data and tool results for numbers.
- Prioritise actions by risk and deadline.
- Assign actions to roles.
- State uncertainties.
- Return structured JSON.

## 34.3 Advisory Drafting Prompt

### Inputs

- Village risk
- Nearest reachable shelter
- Stage and timing
- Audience
- Approved template

### Requirements

- Include all mandatory fields (what, where, when, action, shelter, authority).
- Use short, clear sentences.
- Follow the approved template.
- Return structured JSON for translation and CAP generation.

---

# 35. AI Safety & Trust

The platform must distinguish between:

```text
Official Forecast / Observed Data
      ↓
Model Estimates (surge, flood, exposure)
      ↓
AI Interpretation
      ↓
Recommendation / Advisory
```

### Requirements

- Never fabricate forecast, hazard or exposure numbers.
- Always label the surge model as a screening estimate.
- Defer to official forecasts and warnings.
- Show uncertainty ranges.
- Require human approval for every advisory.
- Enforce mandatory advisory fields.
- Prefer caution (slight over-warning) for life-safety decisions.
- Label parametric estimates as planning estimates, not payout decisions.
- Keep a full audit log of what was sent, when and by whom.

---

# 36. Data Freshness

Every data source should expose freshness metadata.

Example:

```text
Official Bulletin
Issued: 45 minutes ago

Weather Forecast
Run: 06:00 UTC today

Satellite Rainfall
Updated: 30 minutes ago

Shelter List
Updated: June 2026 (state list)

Building Footprints
Dataset version: v3
```

The officer should understand whether the analysis is based on:

- The latest bulletin
- An older forecast run
- Static base data

When a newer bulletin is available, the dashboard shows that the analysis is out of date.

---

# 37. API Architecture

## Scenarios & Forecasts

```http
POST /api/scenarios                 (live or replay)
GET  /api/scenarios/:id
POST /api/bulletins/parse
POST /api/scenarios/:id/track/verify
```

## Hazards

```http
POST /api/scenarios/:id/surge
POST /api/scenarios/:id/flood
GET  /api/scenarios/:id/hazards?layer=
```

## Exposure

```http
GET /api/scenarios/:id/exposure?district=
GET /api/scenarios/:id/villages?sort=risk
GET /api/scenarios/:id/shelters/reachability
```

## Situation & Advisories

```http
POST /api/scenarios/:id/sitrep
POST /api/advisories/draft
POST /api/advisories/:id/approve
POST /api/advisories/:id/dispatch
GET  /api/advisories/:id/cap
GET  /api/advisories?scenario=
```

## Parametric

```http
GET  /api/parametric/policies
POST /api/scenarios/:id/parametric
POST /api/parametric/:id/verify
```

## Language / Voice

```http
POST /api/translate
POST /api/text-to-speech
```

## State / Analytics

```http
GET /api/states
GET /api/states/:id/analytics
GET /api/scenarios/:id/validation
```

---

# 38. Functional Requirements

## FR-01: Scenario Setup

The system must allow an officer or demo user to start a scenario.

### Acceptance Criteria

- User can select a live forecast or a past-cyclone replay.
- Bulletin can be uploaded or fetched.
- Gemini extracts the track and the officer can verify it.

---

## FR-02: Track & Wind

### Acceptance Criteria

- Track uncertainty cone is displayed.
- Wind swath is displayed.

---

## FR-03: Storm Surge Simulation

### Acceptance Criteria

- Surge height is estimated per coastal segment.
- Inundation area is mapped via Earth Engine.
- "Screening estimate" label is displayed.

---

## FR-04: Rainfall Flood Likelihood

### Acceptance Criteria

- Flood-likelihood map is displayed.
- The model is trained on past flood extents.
- Validation against a past cyclone is documented.

---

## FR-05: Exposure & Village Risk

### Acceptance Criteria

- Exposed population is displayed.
- Exposed substations, roads, hospitals and shelters are displayed.
- Village risk score is displayed with a breakdown.
- Shelter reachability (cut-off) is displayed.

---

## FR-06: Gemini Situation Report

### Acceptance Criteria

- Gemini 3.7 Flash uses map images and the bulletin as inputs.
- A structured situation report is displayed.
- Actions are assigned to roles with deadlines.
- Every number matches the underlying data.

---

## FR-07: Advisory Dispatch

### Acceptance Criteria

- Advisories are drafted per area, audience and language.
- Officer can review and approve.
- CAP 1.2 message is generated.
- Sandbox dispatch (SMS / messaging / voice) works.
- Dispatch is logged.

---

## FR-08: Multilingual & Voice

### Acceptance Criteria

- Advisory is available in English, Odia and Bengali.
- At least one advisory is played as audio.
- Mandatory fields are preserved across languages.

---

## FR-09: Parametric Estimate

### Acceptance Criteria

- Trigger probability is displayed for at least one zone.
- Expected payout range is displayed (sample policy).
- Post-event verification is shown for the replay.

---

## FR-10: Dashboards

### Acceptance Criteria

District Officer can view:

- Forecast, hazards, exposure and actions for their district
- Advisory status

State EOC Officer can view:

- District comparison
- Advisory log
- Parametric panel

---

## FR-11: Interoperability

### Acceptance Criteria

The prototype demonstrates:

- Canonical disaster risk schema.
- At least two state configurations.
- State-specific shelter / asset data mapped into the common model.
- Shared services operating on the common model.

---

# 39. Non-Functional Requirements

## Performance

- Fast initial application load
- Standard API response under about 2 seconds where practical
- Full forecast → advisory draft pipeline within minutes (so it can re-run on each bulletin)
- Clear progress states for long geospatial jobs

## Scalability

The system should support:

- Multiple states and countries
- Multiple concurrent scenarios
- Large geospatial layers (processed server-side in Earth Engine)
- Horizontal cloud scaling

## Reliability

- Keep working if one data source fails, and show which inputs are missing.
- Cache base layers and last-known-good results.
- Never lose approved advisories or dispatch logs.
- High availability is critical during cyclone season.

## Accessibility

- Works on laptops in control rooms and on tablets or phones in the field
- Clear, high-contrast maps
- Regional-language advisories
- Voice advisories for low-literacy audiences

## Security

- HTTPS
- Protect API secrets
- Authenticated APIs
- Role-based access
- Strict control over who can approve and dispatch advisories
- Tamper-evident dispatch logs
- Least-privilege cloud permissions

---

# 40. State Onboarding Architecture

A new state (or country) can be onboarded without rewriting the core application.

## Onboarding Flow

```text
Register State / Country
      ↓
Define Coastline, Districts, Villages
      ↓
Register Data Sources (shelters, assets, forecast source)
      ↓
Map Local Fields to Canonical Schema
      ↓
Validate Data
      ↓
Prepare Earth Engine Base Layers
      ↓
Calibrate Surge Model / Fine-tune Flood Model
      ↓
Configure Languages, Advisory Templates, Alert Gateway
      ↓
Enable APIs
      ↓
State Becomes Available
```

## Example

```text
State: West Bengal

State Shelter & Asset Lists
     ↓
WB Adapter
     ↓
Canonical Schema
     ↓
Shared Hazard, Exposure & AI Services
```

The same pattern can be used for Andhra Pradesh, Tamil Nadu, or coastal districts of Bangladesh or Myanmar.

---

# 41. Repository Structure

```text
cyclone-risk-network/
│
├── apps/
│   ├── district-dashboard/
│   └── state-eoc-dashboard/
│
├── services/
│   ├── api/
│   ├── forecast-ingest/
│   ├── surge/
│   ├── flood-model/
│   ├── exposure/
│   ├── situation-reasoning/
│   ├── advisories-cap/
│   ├── parametric/
│   └── localization/
│
├── geospatial/
│   ├── earth-engine/
│   └── networks/
│
├── ai/
│   ├── prompts/
│   ├── schemas/
│   ├── models/
│   └── evaluation/
│
├── data/
│   ├── schemas/
│   ├── adapters/
│   ├── sample/
│   └── replays/
│
├── infrastructure/
│   ├── cloud-run/
│   ├── bigquery/
│   └── firebase/
│
├── docs/
│
└── README.md
```

---

# 42. MVP Data Strategy

Prioritise **real or realistic** data over complicated ingestion.

## Use real / public data where feasible

- Past cyclone bulletins and best tracks
- Earth Engine layers (elevation, radar flood extents, rainfall, buildings, population)
- OpenStreetMap roads, power and hospitals
- Published state shelter lists

## Use realistic sample data where needed

- **Parametric policies**: sample zones, triggers and payout amounts, **clearly labelled sample**.
- **Missing asset data**: sample substations or shelters where public lists are incomplete, clearly labelled.
- **Dispatch**: sandbox channels only.

## Data Source Metadata

Every dataset retains:

- Source
- Observation / issue timestamp
- Dataset version
- Geographic scope
- "Sample" flag where applicable

---

# 43. Recommended MVP Demo Scenarios

## Scenario A

```text
State: Odisha
District: Puri
Cyclone: Fani (May 2019) – replay
Language: Odia
Main hazard: Storm surge + wind
```

## Scenario B

```text
State: West Bengal
District: South 24 Parganas
Cyclone: Amphan (May 2020) – replay
Language: Bengali
Main hazard: Surge + embankment flooding
```

## Scenario C

```text
State: Andhra Pradesh
Coastal delta district
Cyclone: A recent landfall – replay
Language: English / Telugu
Main hazard: Rainfall flooding
```

The number of demo states doesn't matter much. The point is to prove that one platform structure supports different state, hazard and language combinations.

---

# 44. Hackathon Demo Flow

The demo should be one continuous story rather than a collection of disconnected features.

## 0:00–0:30: Introduce the Problem

> 72 hours before a cyclone makes landfall, a district officer in Puri has to decide who to evacuate, what to protect and what to tell people.

## 0:30–1:00: Forecast

Show:

- Bulletin parsed by Gemini
- Track cone and wind swath

## 1:00–1:40: Hazards

Show:

- Storm surge inundation (screening label)
- Rainfall flood likelihood

## 1:40–2:20: Exposure

Show:

- People at risk
- Substations, hospitals, shelters
- Shelters cut off by flooded roads
- Village risk ranking

## 2:20–3:00: Gemini 3.7 Flash Situation Report

Generate the situation report from maps, the bulletin and exposure data. Show role-specific actions.

## 3:00–3:40: Advisory Dispatch

Show:

- Odia advisory draft
- Audio preview
- Officer approval
- CAP message
- Sandbox SMS / voice received

## 3:40–4:00: Parametric Estimate

Show the State EOC panel with trigger probability and expected payout.

## 4:00–4:30: Validation & Interoperability

Show predicted vs observed flooding for the replay. Switch to West Bengal (Amphan) and show the common data structure.

## 4:30–5:00: Scale & Deployment

```text
One Village
   ↓
One District
   ↓
One State
   ↓
All Coastal States
   ↓
Bay of Bengal Region (APAC)
   ↓
Regional Anticipatory Action Network
```

Show the Google AI / Cloud stack powering the solution.

---

# 45. Deployment Architecture

```text
                         Internet
                            │
                            ▼
                    Google Cloud Platform
                            │
                         Cloud Run
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     Next.js App       API Layer         AI Services
          │                 │                 │
          │          Pub/Sub + Scheduler      │
          ▼                 ▼                 ▼
       Firebase         BigQuery          Vertex AI
                                              │
                                              ▼
                                      Gemini 3.7 Flash
                            │
                            ▼
                      External Data
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
     IMD Bulletins     Earth Engine     State Data / Alert Gateway
```

Primary region: `asia-south1` (Mumbai), with `asia-south2` (Delhi) as a disaster-recovery region because availability matters during cyclone season.

---

# 46. Environment & Secrets

Secrets must never be committed to GitHub.

Example configuration:

```text
GEMINI_API_KEY
GOOGLE_CLOUD_PROJECT
GOOGLE_APPLICATION_CREDENTIALS
BIGQUERY_DATASET
FIREBASE_PROJECT_ID
EARTH_ENGINE_PROJECT
MAPS_API_KEY
SMS_SANDBOX_KEY
MESSAGING_SANDBOX_TOKEN
```

Store them in Secret Manager for Cloud Run.

---

# 47. Observability

The system should log:

- API latency
- AI request latency
- AI failures and schema-validation failures
- Earth Engine job duration and failures
- Forecast ingestion events
- Dataset freshness
- Model and prompt version
- Situation report generation events
- Advisory approvals and dispatches (full audit trail)

Future production metrics:

- Warning lead time
- Evacuation coverage
- Advisory delivery success
- Prediction accuracy against observed impacts

---

# 48. AI Evaluation

A basic internal evaluation layer should test:

## Bulletin Parsing

- Accuracy of extracted track points against the source bulletin

## Hazard Models

- Overlap between predicted and observed flood extent (radar satellite) for at least one past cyclone
- Flood model accuracy on a held-out past cyclone

## Exposure

- Share of reported damaged assets or shelters that were flagged (where public reports exist)

## Situation Reports & Advisories

- Every number traceable to data (automated check)
- Mandatory advisory fields present (automated check)
- Actionability (reviewed by the team or a domain mentor)
- Translation quality

## Parametric

- Trigger hit / miss on past cyclones

The hackathon MVP doesn't need a formal scientific evaluation system, but the architecture should make evaluation possible.

---

# 49. Success Metrics

## 49.1 Hackathon Success

The prototype should demonstrate:

- Complete forecast → advisory flow on a past cyclone replay
- Meaningful use of all mandated technologies (Earth Engine, real-time weather, Gemini 3.7 Flash)
- Storm surge simulation
- Rainfall flood likelihood
- Critical infrastructure exposure, including shelter cut-off
- Gemini multimodal situation report
- Approved, multilingual CAP advisory with sandbox dispatch
- Parametric trigger estimate
- Validation against observed flooding
- Multiple state configurations
- Public deployment
- Public or access-granted GitHub repository

## 49.2 Long-Term Impact Metrics

### Life Safety

- Warning lead time for village-level evacuation
- People reached with advisories in their language
- Evacuation coverage of high-risk villages

### Infrastructure & Finance

- Critical assets protected pre-emptively
- Faster restoration of power and roads
- Earlier release of funds through parametric triggers

### Platform Impact

- States and countries integrated
- Districts covered
- Agencies consuming alerts and APIs

---

# 50. Scalability Strategy

## Phase 1: Hackathon

```text
2–3 state configurations
2–3 past cyclone replays
3 languages
Real Earth Engine data + sample policies
```

## Phase 2: District Pilot

```text
1 state disaster management authority
Tabletop exercise with a replayed cyclone
Shadow mode during the live cyclone season (Oct–Dec peak)
```

## Phase 3: State Deployment

```text
All coastal districts of the state
Integration with the state alert gateway (CAP)
Official surge products plugged in
More languages
```

## Phase 4: Regional Network

```text
All Indian coastal states
Neighbouring countries (Bangladesh, Myanmar, Sri Lanka)
Shared data contracts
Shared models
Cross-border alert exchange
```

---

# 51. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Surge model credibility | Screening label, calibration to past events, honest validation, plug-in for official surge products |
| Elevation data inaccuracy in flat deltas | Uncertainty ranges and a cautious bias for life safety |
| AI error in life-safety messages | Human approval, mandatory-field checks, number grounding, reviewed templates and translations |
| Incomplete asset / shelter data | OSM + state lists, a data-gap indicator on the dashboard, request lists during the pilot |
| No live cyclone during the hackathon | Replay mode is the primary demo |
| Slow geospatial processing | Pre-computed base layers, server-side Earth Engine processing, cached results |
| State data incompatibility | Canonical schema + state adapters |
| High AI cost | Run situation reports only on forecast updates or on request |
| Vendor coupling | Abstract AI and data providers behind internal service interfaces |

---

# 52. Security & Privacy

## Personal Data

The platform works with aggregate population data. Dispatch phone numbers (in production) are handled by official alert gateways, not stored in the platform.

## Sensitive Infrastructure Data

Power, hospital and shelter locations may be sensitive. Detailed asset views are restricted to authorised officers.

## Advisories

Approval and dispatch permissions are strictly controlled. Every action is logged.

## Access Control

The MVP supports two roles:

```text
District Disaster Management Officer (scoped to their district; can approve advisories)
State EOC Officer (scoped to their state; read-focused, parametric panel)
```

Role permissions should ensure:

- District officers see and act only on their own district.
- State officers see all districts in their state.
- Only authorised users can approve and dispatch advisories.

---

# 53. Future Roadmap

## Hazard Intelligence

- Official surge product integration
- AI weather ensembles for track uncertainty
- Landslide risk for hilly areas
- Damage prediction from past impacts

## Response Intelligence

- Evacuation planning (village → shelter assignment with transport needs)
- Post-landfall rapid damage assessment from satellite imagery (Gemini multimodal)
- Resource pre-positioning optimisation

## Ecosystem

- Integration with national alerting systems
- Cross-border alert exchange across the Bay of Bengal
- Open hazard and exposure APIs
- Parametric insurance partner integrations

---

# 54. Google AI Integration Map

| Google Technology | Product Role |
|---|---|
| Gemini 3.7 Flash (multimodal) | Bulletin parsing, map + document + table reasoning, situation reports, advisory drafting |
| Vertex AI | Rainfall flood-likelihood model, training and serving |
| Google AI Studio | Prompt experimentation and evaluation |
| Google Earth Engine | Elevation, radar / optical imagery, rainfall, weather fields, buildings, population, surge and flood processing |
| BigQuery | Scenarios, hazards, exposure, advisories, analytics |
| Firebase | Authentication and real-time updates |
| Cloud Run | Backend, geospatial and AI services |
| Google Maps Platform | Map visualisation and road routing |
| Text-to-Speech | Voice advisories |
| Translation API | Multilingual advisories |

---

# 55. Alignment with Hackathon Evaluation

## Problem-Solution Fit: 20%

The product directly addresses:

- Storm surge simulation
- Rainfall damage pathways
- Critical infrastructure exposure
- Automated early-warning dispatch
- Pre-landfall evacuation, hardening and parametric liquidity

## AI / Technical Execution: 25%

The prototype shows meaningful roles for:

- Gemini 3.7 Flash multimodal reasoning (mandated)
- Google Earth Engine (mandated)
- Real-time weather data (mandated)
- A Vertex AI flood model
- Structured AI orchestration with validation

## Depth & Reach Across India: 20%

The architecture shows:

- A state-independent data model
- Multi-state configuration
- Multi-language advisories
- Global Earth Engine layers that make other coasts easy to add
- Standards-based alerts

## Impact Potential: 15%

The solution targets a large coastal population exposed to cyclones. It aims to save lives, protect infrastructure and speed up financial support.

## Deployability & Scalability: 20%

The prototype shows:

- Cloud-native services
- API-first architecture
- State adapters
- Standardised schemas and CAP alerts
- A deployable application
- A realistic shadow-mode pilot path

---

# 56. Definition of Done: Hackathon MVP

## District Officer Experience

- [ ] Officer can access the application.
- [ ] Officer can start a live or replay scenario.
- [ ] Bulletin is parsed and the track can be verified.
- [ ] Track cone and wind swath are displayed.
- [ ] Surge inundation is displayed (with screening label).
- [ ] Rainfall flood likelihood is displayed.
- [ ] Exposure and village risk are displayed.
- [ ] Shelter cut-offs are displayed.

## AI Experience

- [ ] Gemini 3.7 Flash generates a multimodal situation report.
- [ ] Actions are assigned to roles with deadlines.
- [ ] Advisory drafts are generated.
- [ ] Numbers are validated against data.
- [ ] Uncertainty is displayed.

## Advisory & Language

- [ ] English supported.
- [ ] Odia supported.
- [ ] Bengali supported.
- [ ] Officer can approve an advisory.
- [ ] CAP message is generated.
- [ ] Sandbox dispatch works.
- [ ] At least one voice advisory works.

## State EOC Officer

- [ ] State dashboard exists.
- [ ] District comparison is visible.
- [ ] Parametric trigger estimate is visible.

## Interoperability

- [ ] Canonical schema is documented.
- [ ] At least two state configurations exist.
- [ ] State-specific data maps to the common schema.
- [ ] Shared services operate on the common structure.

## Deployment & Submission

- [ ] Prototype is publicly deployed.
- [ ] Source code is available through GitHub.
- [ ] README contains setup and architecture documentation.
- [ ] Demo data and replays are available and labelled.
- [ ] 3–5 minute demo video is prepared.
- [ ] 10–12 slide pitch deck is prepared.
- [ ] 2–3 line product description is prepared.

---

# 57. Recommended Build Priority

Prioritise **one polished end-to-end journey over many disconnected features**.

## Priority 1: Core Experience

```text
Replay Scenario + Gemini Bulletin Parsing
 ↓
Surge + Flood Hazards (Earth Engine)
 ↓
Exposure + Village Risk + Shelter Cut-off
 ↓
Gemini 3.7 Flash Situation Report
 ↓
Advisory Draft + Approval + CAP
```

## Priority 2: Accessibility

```text
Multilingual advisories
 ↓
Voice advisory
 ↓
Sandbox dispatch
```

## Priority 3: Scale Story

```text
State EOC Dashboard
 ↓
Multi-state configurations
 ↓
Validation against observed flooding
```

## Priority 4: Future / Optional

```text
Parametric panel (keep a simple version, because the brief names it)
Live forecast mode
Post-landfall damage assessment
Evacuation planner
```

Don't sacrifice the core forecast-to-advisory journey to add lower-priority features.

---

# 58. Final Product Definition

The solution is an **AI-powered interoperable cyclone anticipatory action network** for India's coasts and the wider Bay of Bengal region.

At the district level:

```text
       OFFICIAL FORECAST + REAL-TIME WEATHER
                       │
                       ▼
             EARTH ENGINE SATELLITE DATA
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      STORM SURGE   RAINFALL     EXPOSURE
                    FLOODING   (power, roads,
                               hospitals, shelters)
          │            │            │
          └────────────┼────────────┘
                       ▼
               AI RISK BRAIN
       Gemini 3.7 Flash + Vertex AI
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Situation    Village Risk   Parametric
       Report      & Actions      Estimate
          │            │            │
          └────────────┼────────────┘
                       ▼
       Approved Multilingual Advisory (CAP / Voice)
                       │
                       ▼
             ACTION BEFORE LANDFALL
```

At the infrastructure level:

```text
     REGIONAL ANTICIPATORY ACTION NETWORK
                    │
           COMMON DATA MODEL
                    │
       ┌────────────┼────────────┐
       │            │            │
    Odisha     West Bengal   Andhra Pradesh
       │            │            │
   Local Data   Local Data   Local Data
       │            │            │
       └────────────┼────────────┘
                    │
            Shared AI Services
                    │
         Shared APIs + CAP Alerts
```

The platform combines:

**Satellite intelligence + real-time weather + multimodal AI reasoning + predictive modelling + multilingual early warning + interoperable disaster infrastructure**

in one scalable architecture.

The hackathon MVP should prove that the solution can move from:

> **One village → One district → One state → All coastal states → The Bay of Bengal region**
