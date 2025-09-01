
import re, json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None

# --- helpers ---
def _to_crore(num: float, unit: str) -> float:
    unit = (unit or "").lower()
    if unit.startswith("crore") or unit.startswith("cr"):
        return num
    if unit.startswith("lakh"):
        return num / 100.0
    if unit.startswith("billion"):
        # 1 billion = 100 crore
        return num * 100.0
    if unit.startswith("million"):
        # 1 million = 0.1 crore
        return num * 0.1
    return num  # assume already crore

AMT_REGEX = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*(crore|cr|billion|million|lakh)?", re.I)
TIMELINE_REGEX = re.compile(r"(?:in|within|over)\s+(\d{1,3})\s+(months?|quarters?)", re.I)
COUNTERPARTY_REGEX = re.compile(r"(?:with|by|from|awarded by|client)\s+([A-Z][A-Za-z0-9&.,\- ]{2,})", re.I)

def parse_text_fields(text: str):
    text = text or ""
    # amount to crore
    amt_cr = 0.0
    m = AMT_REGEX.search(text)
    if m:
        n = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "crore")
        amt_cr = _to_crore(n, unit)
    # timeline
    months = 0
    t = TIMELINE_REGEX.search(text)
    if t:
        n = int(t.group(1))
        unit = t.group(2).lower()
        months = n*3 if unit.startswith("quarter") else n
    # counterparty
    cp = ""
    c = COUNTERPARTY_REGEX.search(text)
    if c:
        cp = c.group(1).strip().rstrip(".")
    return amt_cr, months, cp

def parse_sample_fallback(html_path: Path, limit: int = 20) -> List[Dict]:
    html = html_path.read_text(encoding="utf-8")
    from bs4 import BeautifulSoup as BS
    soup = BS(html, "html.parser")
    items = []
    for li in soup.select("ul.ann-list > li")[:limit]:
        date = li.get("data-date") or ""
        company = li.get("data-company") or ""
        headline = li.select_one("a.title").get_text(strip=True) if li.select_one("a.title") else ""
        body = li.select_one("div.body").get_text(" ", strip=True) if li.select_one("div.body") else ""
        amt_cr, months, cp = parse_text_fields(headline + " " + body)
        has_attach = 1 if "Attachment" in body or "attachment" in body.lower() else 0
        ann_type = "Approval" if "approval" in (headline+body).lower() else ("Order Win" if "order" in (headline+body).lower() else ("Partnership" if "partnership" in (headline+body).lower() else "General"))
        items.append({
            "date": date, "company": company, "sector": "", "ann_type": ann_type,
            "headline": headline, "body": body, "claimed_deal_cr": amt_cr,
            "counterparty": cp, "timeline_months": months, "has_attachment": has_attach
        })
    return items

def fetch_bse_latest(limit: int = 20, use_online: bool = True) -> List[Dict]:
    """
    Tries to fetch BSE announcements online. If it fails or BeautifulSoup/requests isn't available,
    falls back to parsing samples/bse_sample.html (offline-safe). Returns a list of dicts in our schema.
    """
    if use_online and requests is not None and BeautifulSoup is not None:
        try:
            # NOTE: This is a placeholder URL. Adjust selectors/URL to the current BSE announcements page structure.
            url = "https://www.bseindia.com/corporates/ann.html"
            headers = {"User-Agent": "CredibilityPro/1.0 (research; respectful fetch)"}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.select("table tr") or []
            items = []
            for tr in rows[: limit+1]:
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(tds) < 3:
                    continue
                # Heuristic: [date, company, headline] — this may need adjustment for real page structure.
                date, company, headline = tds[0], tds[1], tds[2]
                body = headline
                amt_cr, months, cp = parse_text_fields(headline + " " + body)
                ann_type = "Approval" if "approval" in headline.lower() else ("Order Win" if "order" in headline.lower() else ("Partnership" if "partnership" in headline.lower() else "General"))
                items.append({
                    "date": date, "company": company, "sector": "", "ann_type": ann_type,
                    "headline": headline, "body": body, "claimed_deal_cr": amt_cr,
                    "counterparty": cp, "timeline_months": months, "has_attachment": 0
                })
            if items:
                return items[:limit]
        except Exception:
            pass
    # fallback
    return parse_sample_fallback(Path("samples/bse_sample.html"), limit=limit)
