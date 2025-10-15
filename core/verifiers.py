import re, requests
from typing import Dict
from config.settings import VIRUSTOTAL_API_KEY, URLSCAN_API_KEY

SEBI_IA_PATTERN = re.compile(r"^IA\d{6}$", re.I)
SEBI_RA_PATTERN = re.compile(r"^INA\d{6}$", re.I)
ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$", re.I)
LEI_PATTERN = re.compile(r"^[0-9A-Z]{18}[0-9]{2}$", re.I)
CIN_PATTERN = re.compile(r"^[UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$", re.I)

def valid_sebi_id(text: str) -> bool:
    return bool(SEBI_IA_PATTERN.match(text) or SEBI_RA_PATTERN.match(text))

def valid_isin(text: str) -> bool:
    return bool(ISIN_PATTERN.match(text))

def valid_lei(text: str) -> bool:
    return bool(LEI_PATTERN.match(text))

def valid_cin(text: str) -> bool:
    return bool(CIN_PATTERN.match(text))

def lei_lookup(name_or_lei: str) -> Dict:
    if valid_lei(name_or_lei):
        url = f"https://api.gleif.org/api/v1/lei-records/{name_or_lei}"
    else:
        q = requests.utils.quote(name_or_lei)
        url = f"https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]={q}&page[size]=5"
    try:
        r = requests.get(url, timeout=20)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {"error": "lookup_failed"}

def vt_domain_report(domain: str) -> Dict:
    if not VIRUSTOTAL_API_KEY:
        return {"error": "no_api_key"}
    try:
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        r = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}", headers=headers, timeout=25)
        return r.json() if r.ok else {"error": f"vt_status_{r.status_code}"}
    except Exception as e:
        return {"error": "vt_exception", "detail": str(e)}

def urlscan_submit(url: str) -> Dict:
    if not URLSCAN_API_KEY:
        return {"error": "no_api_key"}
    try:
        headers = {"API-Key": URLSCAN_API_KEY, "Content-Type": "application/json"}
        payload = {"url": url, "visibility": "unlisted"}
        r = requests.post("https://urlscan.io/api/v1/scan/", headers=headers, json=payload, timeout=25)
        return r.json() if r.status_code in (200, 201) else {"error": f"urlscan_status_{r.status_code}", "text": r.text}
    except Exception as e:
        return {"error": "urlscan_exception", "detail": str(e)}
