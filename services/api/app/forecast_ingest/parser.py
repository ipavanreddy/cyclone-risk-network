"""Deterministic IMD-style bulletin parser. Demo-mode fallback for Gemini bulletin parsing, and a
cross-check for Gemini output. Extracts only what is written in the bulletin; never invents values."""
import re
from datetime import datetime, timedelta, timezone

from app.ai.schemas import BulletinParse, ExpectedLandfall, TrackPoint

IST = timezone(timedelta(hours=5, minutes=30))

ROW = re.compile(
    r"^(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{2})/(?P<hh>\d{2})(?P<mm>\d{2})\s*\|\s*(?P<lat>\d+(?:\.\d+)?)\s*/\s*"
    r"(?P<lon>\d+(?:\.\d+)?)\s*\|\s*(?:(?P<vlo>\d+)\s*-\s*)?(?P<vhi>\d+)[^|]*\|\s*(?P<p>\d+)?\s*\|\s*(?P<cat>[A-Za-z]+)?",
    re.MULTILINE,
)
ISSUED = re.compile(r"Issued at:\s*(?P<hh>\d{2})(?P<mm>\d{2})\s*IST,\s*(?P<date>\d{1,2} \w+ \d{4})")
NAME = re.compile(r"'(?P<name>[A-Z][A-Z]+)'")
BULLETIN_NO = re.compile(r"Bulletin No\.?:\s*(?P<no>\S+)")
LANDFALL = re.compile(r"cross the (?P<coast>.+?) (?P<area>(?:near|across|between) .+?) during the "
                      r"(?P<part>forenoon|afternoon|evening|night) of (?P<date>\d{1,2} \w+ \d{4})", re.DOTALL)
SURGE = re.compile(r"Storm surge:\s*(?P<text>[^\n]+)")
PART_HOURS = {"forenoon": 9, "afternoon": 14, "evening": 18, "night": 22}


def parse_bulletin(text: str) -> BulletinParse:
    rows = []
    for m in ROW.finditer(text):
        t = datetime(2000 + int(m["y"]), int(m["m"]), int(m["d"]), int(m["hh"]), int(m["mm"]), tzinfo=IST)
        rows.append(TrackPoint(time=t.isoformat(), lat=float(m["lat"]), lon=float(m["lon"]),
                               max_wind_kmh=int(m["vhi"]), central_pressure_hpa=int(m["p"]) if m["p"] else None,
                               category=m["cat"]))
    issued = ISSUED.search(text)
    issued_at = ""
    if issued:
        d = datetime.strptime(f"{issued['date']} {issued['hh']}{issued['mm']}", "%d %B %Y %H%M").replace(tzinfo=IST)
        issued_at = d.isoformat()
    name = NAME.search(text)
    lf = LANDFALL.search(text)
    landfall = ExpectedLandfall(area="not stated", time="not stated")
    if lf:
        day = datetime.strptime(lf["date"], "%d %B %Y").replace(tzinfo=IST)
        landfall = ExpectedLandfall(area=" ".join(lf["area"].split()),
                                    time=day.replace(hour=PART_HOURS[lf["part"]]).isoformat())
    surge = SURGE.search(text)
    no = BULLETIN_NO.search(text)
    found = sum([bool(rows), bool(issued), bool(name), bool(lf)])
    return BulletinParse(
        cyclone_name=name["name"].title() if name else "unknown",
        bulletin_no=no["no"] if no else None,
        issued_at=issued_at,
        track=rows,
        expected_landfall=landfall,
        official_surge_text=surge["text"].strip() if surge else None,
        confidence=round(found / 4 * 0.95, 2),
        requires_human_review=True,
    )
