// TatRaksha pitch deck (Track 5). Build: `npm install && node build-deck.js` in docs/pitch.
// Output: TatRaksha_Spontom_Pitch.pptx. Layouts and styling live in deck-kit.js (Spontom deck kit).
//
// Every number on these slides comes from docs/PRD.md, from the running app on the Fani 2019 replay
// (sample data, synthetic terrain grid, captured 30 Sep 2026) or from a numbered reference.
const kit = require("./deck-kit");

// ---- Live links: edit here (e.g. swap in Firebase Hosting URLs later) ----
const LINKS = [
  { label: "District dashboard", url: "https://cyclone-risk-network-district-dashboard-847963771142.asia-south1.run.app" },
  { label: "State EOC dashboard", url: "https://cyclone-risk-network-state-eoc-dashboard-847963771142.asia-south1.run.app" },
  { label: "API (/docs)", url: "https://cyclone-risk-network-api-847963771142.asia-south1.run.app/docs" },
  { label: "Source", url: "https://github.com/ipavanreddy/cyclone-risk-network" },
];
// Displayed without the scheme so long Cloud Run URLs fit on one line; the hyperlink keeps https.
LINKS.forEach((l) => { l.text = l.text || l.url.replace(/^https:\/\//, ""); });

const A = (f) => __dirname + "/assets/" + f;

const content = {
  meta: { product: "TatRaksha", title: "Cyclone anticipatory action pitch" },
  slides: [
    // 1 ─ Cover
    { type: "cover", kicker: "Build with AI (Google)  •  Track 5", product: "TatRaksha",
      tagline: "From a cyclone bulletin\nto village-level action.",
      subtitle: "Impact forecasts, a Gemini situation report and approved multilingual warnings for Bay of Bengal districts.",
      pills: ["Gemini 3.7 Flash", "Human-approved"], image: A("cover-puri-hazard-map.jpg"),
      imageCaption: "App screenshot: Fani 2019 replay, Puri, T-24h (sample data). Map © OpenStreetMap contributors (ODbL).",
      byline: "A prototype by Spontom Enterprise Private Limited", dateline: "DPIIT Recognised  •  Visakhapatnam  •  September 2026",
      notes: "TatRaksha, meaning coast protector, turns an official IMD cyclone bulletin into village-level action up to 72 hours before landfall. The image is a real screenshot of our district dashboard replaying Cyclone Fani over Puri at T-24 hours. Gemini 3.7 Flash reads the bulletin and the hazard map, transparent models rank every village, and the district officer approves every warning. Everything you see is running code; replay data is sample data and labelled as such." },

    // 2 ─ Problem
    { type: "problem", section: "01 — Problem understanding", title: "The forecast is regional. The decisions are local.",
      subtitle: "A district officer must turn each new bulletin into who to evacuate, what to protect and what to say.",
      card: { heading: "One bulletin. Hundreds of local decisions.", stats: [{ n: "72", label: "hours" }, { n: "30", label: "villages" }, { n: "1", label: "officer" }],
        story: "Fani replay, T-24h: 59,600 people in high-risk villages; 5 villages with no shelter reachable by road.", pill: "LOCAL-IMPACT GAP" },
      flow: [{ title: "BULLETIN", desc: "Track, wind, surge text" }, { title: "COMPILE", desc: "Lists, maps, phone calls" }, { title: "?", desc: "Who floods? Which road cuts?", gap: true }, { title: "WARN", desc: "Drafted by hand, per language" }],
      focused: "Officers lack a village-level impact picture that updates with every bulletin.",
      consequence: "Evacuation is late or mistargeted, shelters turn out unreachable, warnings lag in local languages.",
      footnote: "[1] IMD RSMC bulletins give regional track/surge guidance.  [7] Replay figures: TatRaksha Fani 2019 sample data (synthetic terrain), not official statistics.",
      notes: "IMD issues excellent regional bulletins: track, intensity and surge guidance for a coastline. But the district officer has to answer local questions: which villages flood, which roads get cut, which shelters become unreachable, and what to tell people in Odia. Today that means compiling lists and making phone calls, again for every new bulletin. In our Fani replay at T-24 hours, 59,600 people are in high-risk villages and five villages have no shelter reachable by road. Those numbers come from our sample replay data, not official statistics." },

    // 3 ─ Solution
    { type: "solution", section: "02 — Proposed solution", title: "TatRaksha turns each bulletin into an approved warning.",
      subtitle: "One pipeline from the official forecast to a CAP 1.2 alert, with a human decision at the end.",
      steps: [{ title: "IMPACT FORECAST", desc: "Surge, rain-flood and wind give every village a transparent Village Risk score." },
        { title: "GEMINI REASONING", desc: "Multimodal situation report from hazard map, bulletin and tables; numbers checked.", highlight: true },
        { title: "APPROVED WARNING", desc: "Odia, Bengali or English advisory; officer approves; CAP 1.2; sandbox dispatch.", coral: true }],
      panel: { header: "ADVISORY DRAFT  •  SATAPADA", badge: "Needs approval", title: "Evacuation order • Fani • T-24h • English",
        items: ["What: winds up to 170 km/h, heavy rain and flooding", "Where: Satapada, Krushnaprasad block, Puri", "When: from 02-05-2019 17:27 IST", "Action: Leave now for the cyclone shelter. Do not wait."],
        fallback: "No shelter reachable by road: strong building on high ground; call 1070.", footer: "Issued by Collector & DM, Puri (DDMA)", button: "Approve → CAP" },
      footnote: "Real output of the app (advisory_v1, gemini-3.7-flash) on the Fani 2019 replay at T-24h; replay data are samples. [4] OASIS CAP 1.2.",
      notes: "TatRaksha is one pipeline. First, an impact forecast: screening surge, rainfall flood likelihood and wind give every village a transparent Village Risk score. Second, Gemini 3.7 Flash writes a situation report from the hazard map image, the bulletin and the exposure tables, and every number is checked against the data. Third, an advisory with six mandatory fields, which the officer must approve before it becomes a CAP 1.2 message. On the right is the real draft the app produced for Satapada, a village the road model found has no reachable shelter." },

    // 4 ─ How it works
    { type: "loop", section: "03 — How it works", title: "Every new bulletin re-runs the whole chain.",
      subtitle: "Observed data, model estimates, AI interpretation and recommendation stay separate and labelled.", highlight: 4,
      flow: [{ title: "Parse", desc: "Gemini reads bulletin" }, { title: "Verify", desc: "Officer checks track" }, { title: "Hazards", desc: "Surge, flood, wind" }, { title: "Exposure", desc: "Risk + road cut-off" }, { title: "Sitrep", desc: "Multimodal Gemini" }, { title: "Approve", desc: "Advisory → CAP 1.2" }, { title: "Dispatch", desc: "Sandbox + audit" }],
      tiers: [{ label: "Auto • per bulletin", text: "Parse, 9-track set, hazards, Village Risk, cut-offs and sitrep draft re-run on each update." },
        { label: "Officer • decides", text: "Verifies the track, reviews translations, approves or edits each advisory before dispatch." },
        { label: "State EOC • compares", text: "Sees districts side by side, advisory logs and parametric trigger estimates." }],
      assumptionLabel: "Human gate", assumption: "No advisory is dispatched without the district officer's approval; parametric numbers are planning estimates.",
      footnote: "Journey per PRD §8. Warning stages follow the PRD: T-72h Watch → T-48h Warning → T-24h Evacuation Order → T-6h Final Warning.",
      notes: "Here is the loop. Gemini parses the bulletin, and a deterministic parser cross-checks it before the officer verifies the track. The hazard models, the exposure and road cut-off analysis and the situation report all re-run automatically whenever a new bulletin arrives. The officer stays in charge of every consequential step, and the State EOC sees all districts plus parametric trigger estimates. Nothing reaches the public without human approval." },

    // 5 ─ Users
    { type: "users", section: "04 — Users & context", title: "Built for the district officer, useful to the state.",
      subtitle: "Two app roles only. Everyone else receives role-specific actions or public advisories.",
      image: A("users-sitrep-actions.jpg"), imageLabel: "District officer  •  Primary user",
      imageCaption: "Gemini sitrep: actions by role, with deadlines and evidence",
      people: [{ name: "State EOC Officer", role: "Secondary user", desc: "Compares districts, reviews advisories, sees parametric triggers." },
        { name: "Collector & DM", role: "Issuing authority", desc: "Named on every advisory; approval runs through the DDMA." },
        { name: "Line departments", role: "Action owners", desc: "Power, health, police, fisheries get tasks with deadlines, e.g. power by T-8h." },
        { name: "Coastal public", role: "Recipients", desc: "Fishers and villagers get warnings in Odia, Bengali or English; no app login." }],
      constraints: [{ label: "Updates", text: "re-run per bulletin" }, { label: "Languages", text: "templates + voice" }, { label: "Data gaps", text: "labels + freshness" }],
      footnote: "Roles from PRD §7. Screenshot: live sitrep on the Fani replay (gemini-3.7-flash, sitrep_v1); figures are from sample data.",
      notes: "Our primary user is the District Disaster Management Officer: accountable, time-pressed and coordinating many departments. The State EOC Officer is the second role, with a read-focused view across districts. The Collector's name goes on every advisory, line departments receive actions with deadlines, and the public receives warnings without ever logging in. The screenshot shows what the officer gets from Gemini: actions by role, each with a deadline and the data behind it." },

    // 6 ─ Journey
    { type: "journey", section: "05 — Journey", title: "Fani 2019 replay: Satapada at T-24 hours.",
      subtitle: "Scenario A of PRD §43: Odisha, Puri district, Odia, storm surge plus wind. All figures from sample replay data.",
      steps: [{ label: "T-72h Watch", title: "Bulletin parsed", desc: "14,100 people in 3 high-risk villages." },
        { label: "T-24h update", title: "Hazards re-run", desc: "Surge 1.66 m expected, 1.89 m high; cone 77 km." },
        { label: "Exposure", title: "Satapada: risk 61", desc: "No shelter reachable by road; 2 roads cut.", highlight: true },
        { label: "Advisory", title: "Officer approves", desc: "Odia draft, back-translated, then CAP 1.2." }],
      panel: { kicker: "Gemini situation report • T-24h", headline: "Evacuate by T-12h.", sub: "Evidence-linked actions:",
        items: ["59,600 people in high-risk villages", "Power: 5 substations by T-8h", "Penthakata: 23,600 assigned, 1,650 seats"],
        whyLabel: "Why trust it", why: "Numbers checked against the pipeline (grounded: true); model, version and prompt stored with the report." },
      footnote: "Sample data on the synthetic terrain grid; surge is a screening estimate – defer to official surge guidance. Captured from the app, 30 Sep 2026.",
      notes: "Let me walk through the demo. At T-72 hours Gemini parses the bulletin and three villages with 14,100 people are already high risk. At T-24 hours the hazards re-run: expected surge 1.66 metres, high case 1.89, and the network model finds two roads cut. Satapada scores 61 and has no shelter reachable by road, so its advisory tells people to go to a strong building on high ground and call 1070. Gemini's report sets the deadline and flags that one shelter is assigned far more people than it can hold." },

    // 7 ─ Differentiation
    { type: "table", section: "06 — Innovation & differentiation", title: "Not a new forecast. The missing local-impact layer.",
      subtitle: "India's systems forecast and disseminate well; TatRaksha connects the forecast to village-level decisions.",
      columns: ["Approach", "What it contributes", "Remaining boundary / gap"],
      rows: [["IMD RSMC bulletins", "Authoritative track, intensity, surge guidance", "Coast/district scale; local impact is compiled by hand"],
        ["INCOIS ocean services", "Storm-surge and high-wave forecasts for the coast", "Hazard, not people, shelters or roads"],
        ["NDMA SACHET (CAP)", "Standard, geo-targeted alert dissemination", "Delivers a message; does not decide who or what"],
        ["Generic AI assistant", "Fast drafting and summarising", "No grounding, approval gate or audit trail"],
        ["TatRaksha", "Village risk + road cut-off + grounded Gemini sitrep + CAP", "Screening models; needs field validation; unproven"]],
      callout: "Feeds official forecasts in and CAP alerts out: it complements, not replaces, national systems.",
      footnote: "[1] IMD RSMC New Delhi.  [2] INCOIS.  [3] NDMA SACHET.  TatRaksha consumes official forecasts and defers to official surge guidance.",
      notes: "We are not building another forecast or another alert gateway. IMD provides the authoritative forecast, INCOIS the ocean-state and surge products, and NDMA's CAP-based SACHET system delivers the alert. What sits between them today is manual work: which villages, which roads, which shelters, which words. TatRaksha fills that gap, and because it outputs CAP 1.2 it plugs into the existing alert infrastructure. Our honest boundary: the hazard models are screening level and need field validation." },

    // 8 ─ Technology
    { type: "tech", section: "07 — Technology & Google AI", title: "Bounded Gemini on transparent hazard models.",
      subtitle: "Gemini reads and reasons; it never measures. Every AI output is schema-validated JSON.",
      rows: [{ title: "Official inputs", desc: "IMD bulletin text/PDF • state adapter JSON • canonical schema" },
        { title: "Hazard engine", desc: "Screening surge • rain-flood heuristic • Rankine wind • 9-track set" },
        { title: "Exposure + routing", desc: "Village Risk 30/25/15/15/15 • road cut-off • Google Routes" },
        { title: "Gemini layer", desc: "Gemini 3.7 Flash: parse, multimodal sitrep, drafts; versioned prompts", highlight: true },
        { title: "Delivery + audit", desc: "CAP 1.2 • TTS/STT • sandbox dispatch • BigQuery audit • Cloud Run" }],
      navy: { title: "Google AI integration map", bullets: ["Live: Gemini 3.7 Flash on Vertex AI", "Live: Maps Routes, Translation, TTS, STT", "Live: BigQuery audit, Cloud Storage archive"],
        pillLabel: "Next", pillText: "Earth Engine layers wired; Vertex AI flood model." },
      gate: { title: "Real vs demo, and freshness", rows: [{ label: "Startup probe", text: "One live call per integration; the badge shows what truly works" },
        { label: "Sample flag", text: "Replay data carry is_sample in the data and the UI" },
        { label: "Stale input", text: "A newer bulletin marks the analysis out of date", coral: true }] },
      footnote: "[6] Earth Engine data catalog. Rain-flood likelihood is a transparent heuristic until the Vertex AI model is trained (PRD §12).",
      notes: "The architecture is layered. Hazards and exposure are transparent formulas an officer can explain, so Gemini is never asked to invent a measurement. Gemini 3.7 Flash does three bounded jobs: parse the bulletin, reason over the hazard map image and tables for the situation report, and draft English advisories, all as schema-validated JSON with model and prompt versions stored. Maps, Translation, Text-to-Speech, Speech-to-Text, BigQuery and Cloud Storage are live; Earth Engine is wired in, and the Vertex AI flood model is next. A startup probe makes one real call per integration so the badge shows what actually works." },

    // 9 ─ Responsible AI
    { type: "responsible", section: "08 — Responsible AI & data", title: "Life-safety AI must be checkable and overridable.",
      subtitle: "Prefer caution, show uncertainty, and keep a human decision on every warning.",
      left: { pills: ["Human approval", "Every advisory, every dispatch"],
        rows: [{ label: "Grounded numbers", text: "Sitrep figures checked against the pipeline; ungrounded items removed and listed." },
          { label: "Provenance", text: "model_name, model_version and prompt_version stored on every AI record." }] },
      dont: { label: "Do not do / collect", items: ["Invent forecast, surge or exposure numbers", "Store citizens' phone numbers (gateways hold them)", "Send real public alerts from the MVP (sandbox only)"] },
      safety: { title: "Safety by design", rows: [{ label: "Screening label", text: "Surge is shown as a screening estimate; defer to official guidance." },
        { label: "Uncertainty", text: "Track cone, expected vs high surge, and listed uncertainties." },
        { label: "Wording", text: "Odia/Bengali from pre-approved templates; back-translation for review." },
        { label: "Mandatory fields", text: "What, where, when, action, shelter, authority, or rejected." },
        { label: "Access", text: "Two roles; district officers act only on their own district." },
        { label: "Audit", text: "Append-only audit and dispatch logs streamed to BigQuery." }] },
      footnote: "Rules from PRD §35 and §52.  [4] OASIS CAP 1.2.  Odia/Bengali templates are sample translations pending native-speaker review.",
      notes: "In life-safety work, the AI must be checkable and overridable. Every number in the situation report is checked against the pipeline output, and anything ungrounded is removed and shown. Life-safety wording in Odia and Bengali comes from pre-approved templates, with machine back-translation only to help the reviewer. We never invent measurements, never store citizens' phone numbers, and send nothing real from the prototype. Every approval and dispatch lands in an append-only audit log." },

    // 10 ─ Outcomes
    { type: "outcomes", section: "09 — Outcomes, validation & scale", title: "Prove it in shadow mode before anyone relies on it.",
      subtitle: "The first proof is earlier, better-targeted action, not app usage.",
      chain: [{ title: "Lead time", desc: "Village-level warning 24–72 h out" }, { title: "Targeting", desc: "Highest-risk villages move first" }, { title: "Reach", desc: "Warnings in the local language" }, { title: "Liquidity", desc: "Funds prepared before landfall" }],
      measure: { items: ["Predicted vs observed flooding", "Warning lead time per village", "Advisory delivery success", "Trigger hit/miss on past cyclones"] },
      gates: [{ title: "Tabletop", desc: "Replay Fani and Amphan with DDMA staff; score actionability" },
        { title: "Shadow season", desc: "Run beside the official process, Oct–Dec peak; no public alerts" },
        { title: "Claim carefully", desc: "Sample replay: hit rate 1.0, false-alarm ratio 0.5; not a field result" }],
      ownership: { title: "Ownership + scale", rows: [{ label: "Owner", text: "State SDMA (e.g. OSDMA) + DDMAs" }, { label: "Channel", text: "State EOC → DDMAs; CAP to NDMA gateway [3]" }, { label: "Gate", text: "Official surge feed • language review • data MoU" }] },
      budget: { label: "Budget route", text: "Candidate: SDMF / SDRF preparedness and capacity-building windows under XV-FC guidelines; confirm with the SDMA. [8]" },
      footnote: "Phases per PRD §50: district pilot → state → all coastal states → Bay of Bengal (Bangladesh, Myanmar, Sri Lanka). [5] NCRMP shelters and warning systems.",
      notes: "We want to earn trust before anyone relies on this. Phase one is a tabletop exercise replaying Fani and Amphan with district staff. Phase two runs TatRaksha in shadow mode alongside the official process during the October to December peak, with no public alerts. On our sample replay the validation shows every observed flooded village was flagged, at a false-alarm ratio of 0.5, which is deliberately cautious but not a field result. The natural owner is the state disaster management authority, funded through the Finance Commission disaster funds, which we still need to confirm with the state." },

    // 11 ─ Live prototype
    { type: "live", section: "10 — Live prototype", title: "Working today, end to end.",
      subtitle: "Two dashboards and one API on Cloud Run (asia-south1). Replays: Odisha / Fani 2019 and West Bengal / Amphan 2020.",
      screens: [{ image: A("screen-district-dashboard.jpg"), caption: "District dashboard: map + Gemini sitrep" }, { image: A("screen-state-eoc.jpg"), caption: "State EOC: district and block comparison" }],
      links: LINKS,
      criteria: [{ weight: "25%", label: "AI / technical execution", how: "Gemini 3.7 Flash parse + multimodal sitrep; schema-validated, grounded" },
        { weight: "20%", label: "Problem-solution fit", how: "Surge, rain-flood, infrastructure exposure and dispatch all built" },
        { weight: "20%", label: "Depth & reach across India", how: "Canonical schema, 2 state adapters, 3 languages, CAP 1.2" },
        { weight: "20%", label: "Deployability & scalability", how: "Cloud Run, one deploy script, labelled demo fallbacks" },
        { weight: "15%", label: "Impact potential", how: "Earlier, targeted evacuation; parametric liquidity (sample policies)" }],
      footnote: "Screenshots from the running app (30 Sep 2026, replay sample data). A new state joins by a JSON adapter, not a code fork.",
      notes: "This is the working prototype. On the left, the district dashboard with the Fani replay map and a live Gemini situation report; on the right, the State EOC comparing blocks and districts. Both run on Cloud Run in Mumbai with the API, and every integration falls back to a labelled demo mode. Against the evaluation criteria: meaningful Gemini use, every clause of the brief built, two states and three languages on one schema, and a one-command deploy. Try it at the links shown." },

    // 12–13 ─ References
    { type: "references", section: "Appendix — References", title: "Forecast, alerting and programme sources",
      subtitle: "Numbered references correspond to citations in the core slides.",
      refs: [{ n: 1, title: "IMD RSMC New Delhi", desc: "Tropical cyclone bulletins and reports, including Fani (2019) and Amphan (2020); used to reconstruct the sample replays.", url: "https://rsmcnewdelhi.imd.gov.in", tag: "OFFICIAL SOURCE" },
        { n: 2, title: "INCOIS", desc: "Indian National Centre for Ocean Information Services: storm-surge and high-wave services for India's coast.", url: "https://incois.gov.in", tag: "OFFICIAL SOURCE" },
        { n: 3, title: "NDMA SACHET", desc: "National Disaster Management Authority's CAP-based integrated alert system for geo-targeted dissemination.", url: "https://sachet.ndma.gov.in", tag: "OFFICIAL SOURCE" },
        { n: 4, title: "OASIS CAP v1.2", desc: "Common Alerting Protocol 1.2 standard; TatRaksha generates and validates CAP 1.2 messages.", url: "https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.html", tag: "STANDARD" }],
      notes: "These are the sources behind the claims on the core slides. IMD's regional centre provides the bulletins we consume and the public facts used to reconstruct our sample replays. INCOIS provides official surge and wave services, and NDMA's SACHET system is the CAP-based alert channel we plug into. CAP 1.2 is the open OASIS standard our advisories follow." },
    { type: "references", section: "Appendix — References", title: "Programme, data and funding sources",
      subtitle: "Numbered references correspond to citations in the core slides.",
      refs: [{ n: 5, title: "NCRMP (NDMA)", desc: "National Cyclone Risk Mitigation Project: multipurpose cyclone shelters and early-warning dissemination in coastal states.", url: "https://mitigation.ndma.gov.in/ncrmp/", tag: "OFFICIAL SOURCE" },
        { n: 6, title: "Earth Engine data catalog", desc: "Copernicus DEM, GPM IMERG rainfall, JRC Surface Water, WorldPop, Open Buildings layers used by the Earth Engine path.", url: "https://developers.google.com/earth-engine/datasets", tag: "DATASETS" },
        { n: 7, title: "TatRaksha replay data (sample)", desc: "data/replays/: reconstructed tracks and bulletins, synthetic terrain, sample villages, shelters, roads; flagged is_sample.", tag: "Local evidence" },
        { n: 8, title: "MHA Disaster Management Division", desc: "SDRF / SDMF guidelines under the XV Finance Commission award; candidate budget route for a state pilot.", url: "https://ndmindia.mha.gov.in", tag: "OFFICIAL SOURCE" }],
      notes: "The National Cyclone Risk Mitigation Project built much of the shelter and warning infrastructure we model. The Earth Engine catalogue lists the open datasets our geospatial path uses. Reference seven is our own sample replay data, clearly flagged in the data and the UI. Reference eight is the Ministry of Home Affairs guidance on state disaster response and mitigation funds, our candidate budget route to confirm with the state." },
  ],
};

kit.build(content, __dirname + "/TatRaksha_Spontom_Pitch.pptx").then((p) => console.log("wrote", p));
