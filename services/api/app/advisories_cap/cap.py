"""CAP 1.2 (OASIS Common Alerting Protocol) message builder and structural validator."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime

CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"
ET.register_namespace("", CAP_NS)

STATUS = {"Actual", "Exercise", "System", "Test", "Draft"}
MSG_TYPE = {"Alert", "Update", "Cancel", "Ack", "Error"}
SCOPE = {"Public", "Restricted", "Private"}
CATEGORY = {"Geo", "Met", "Safety", "Security", "Rescue", "Fire", "Health", "Env", "Transport", "Infra", "CBRNE", "Other"}
RESPONSE = {"Shelter", "Evacuate", "Prepare", "Execute", "Avoid", "Monitor", "Assess", "AllClear", "None"}
URGENCY = {"Immediate", "Expected", "Future", "Past", "Unknown"}
SEVERITY = {"Extreme", "Severe", "Moderate", "Minor", "Unknown"}
CERTAINTY = {"Observed", "Likely", "Possible", "Unlikely", "Unknown"}
CAP_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")
ALERT_ORDER = ["identifier", "sender", "sent", "status", "msgType", "source", "scope", "restriction", "addresses",
               "code", "note", "references", "incidents", "info"]

STAGE_CAP = {
    "watch": ("Future", "Possible", "Prepare"),
    "warning": ("Expected", "Likely", "Prepare"),
    "evacuation_order": ("Immediate", "Likely", "Evacuate"),
    "final_warning": ("Immediate", "Likely", "Evacuate"),
}
BAND_SEVERITY = {"Very High": "Extreme", "High": "Severe", "Moderate": "Moderate", "Low": "Minor"}


def cap_time(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def build(*, identifier: str, sender: str, sent: datetime, status: str, stage: str, risk_band: str, language: str,
          headline: str, description: str, instruction: str, sender_name: str, area_desc: str, lat: float,
          lon: float, radius_km: float, onset: str | None, geocode: tuple[str, str] | None, note: str) -> str:
    urgency, certainty, response = STAGE_CAP[stage]
    alert = ET.Element(f"{{{CAP_NS}}}alert")

    def sub(parent, tag, text=None):
        el = ET.SubElement(parent, f"{{{CAP_NS}}}{tag}")
        if text is not None:
            el.text = text
        return el

    sub(alert, "identifier", identifier)
    sub(alert, "sender", sender)
    sub(alert, "sent", cap_time(sent))
    sub(alert, "status", status)
    sub(alert, "msgType", "Alert")
    sub(alert, "scope", "Public")
    sub(alert, "note", note)
    info = sub(alert, "info")
    sub(info, "language", language)
    sub(info, "category", "Met")
    sub(info, "event", "Tropical Cyclone")
    sub(info, "responseType", response)
    sub(info, "urgency", urgency)
    sub(info, "severity", BAND_SEVERITY.get(risk_band, "Severe"))
    sub(info, "certainty", certainty)
    if onset:
        sub(info, "onset", cap_time(datetime.fromisoformat(onset)))
    sub(info, "senderName", sender_name)
    sub(info, "headline", headline[:160])
    sub(info, "description", description)
    sub(info, "instruction", instruction)
    area = sub(info, "area")
    sub(area, "areaDesc", area_desc)
    sub(area, "circle", f"{lat:.4f},{lon:.4f} {radius_km:.1f}")
    if geocode:
        gc = sub(area, "geocode")
        sub(gc, "valueName", geocode[0])
        sub(gc, "value", geocode[1])
    ET.indent(alert)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(alert, encoding="unicode")


def validate(xml: str) -> list[str]:
    """Structural CAP 1.2 validation (required elements, order, enumerations, time format). [] = valid."""
    errors = []
    try:
        root = ET.fromstring(xml.encode("utf-8"))
    except ET.ParseError as exc:
        return [f"not well-formed XML: {exc}"]
    if root.tag != f"{{{CAP_NS}}}alert":
        return [f"root must be {{{CAP_NS}}}alert, got {root.tag}"]

    def local(el):
        return el.tag.split("}")[-1]

    tags = [local(c) for c in root]
    for req in ["identifier", "sender", "sent", "status", "msgType", "scope"]:
        if req not in tags:
            errors.append(f"missing alert/{req}")
    order = [ALERT_ORDER.index(t) for t in tags if t in ALERT_ORDER]
    if order != sorted(order):
        errors.append("alert child elements out of order")
    unknown = [t for t in tags if t not in ALERT_ORDER]
    if unknown:
        errors.append(f"unknown alert elements {unknown}")

    def text(parent, tag):
        el = parent.find(f"{{{CAP_NS}}}{tag}")
        return el.text if el is not None else None

    if text(root, "status") not in STATUS:
        errors.append("invalid status")
    if text(root, "msgType") not in MSG_TYPE:
        errors.append("invalid msgType")
    if text(root, "scope") not in SCOPE:
        errors.append("invalid scope")
    if not CAP_TIME.match(text(root, "sent") or ""):
        errors.append("sent must be YYYY-MM-DDThh:mm:ss±hh:mm")
    if any(ch in (text(root, "identifier") or " ") for ch in " ,<&"):
        errors.append("identifier contains forbidden characters")
    for info in root.findall(f"{{{CAP_NS}}}info"):
        for tag, allowed in [("category", CATEGORY), ("urgency", URGENCY), ("severity", SEVERITY),
                             ("certainty", CERTAINTY)]:
            if text(info, tag) not in allowed:
                errors.append(f"info/{tag} missing or invalid")
        if not text(info, "event"):
            errors.append("info/event missing")
        rt = text(info, "responseType")
        if rt is not None and rt not in RESPONSE:
            errors.append("info/responseType invalid")
        onset = text(info, "onset")
        if onset is not None and not CAP_TIME.match(onset):
            errors.append("info/onset bad time format")
        for area in info.findall(f"{{{CAP_NS}}}area"):
            if not text(area, "areaDesc"):
                errors.append("area/areaDesc missing")
            circle = text(area, "circle")
            if circle is not None and not re.match(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)? \d+(\.\d+)?$", circle):
                errors.append("area/circle must be 'lat,lon radius'")
    return errors
