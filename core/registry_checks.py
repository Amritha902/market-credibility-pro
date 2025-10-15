# core/registry_checks.py
import re
import requests

# Patterns
LEI_RE = re.compile(r'^[A-Z0-9]{20}$')
ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')
CIN_RE = re.compile(r'^[LUAP][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$', re.IGNORECASE)
SEBI_ID_RE = re.compile(r'^[0-9A-Z\-]{4,20}$')


def validate_lei(lei: str) -> dict:
    lei = lei.strip().upper()
    ok = bool(LEI_RE.match(lei))
    info = {"input": lei, "pattern_valid": ok}
    if ok:
        try:
            url = f"https://api.gleif.org/api/v1/lei-records/{lei}"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                info["gleif"] = resp.json()
        except Exception as e:
            info["gleif_error"] = str(e)
    return info


def validate_isin(isin: str) -> dict:
    isin = isin.strip().upper()
    ok = bool(ISIN_RE.match(isin))
    return {"input": isin, "pattern_valid": ok}


def validate_cin(cin: str) -> dict:
    cin = cin.strip().upper()
    ok = bool(CIN_RE.match(cin))
    return {"input": cin, "pattern_valid": ok}


def validate_sebi_id(sebi_id: str) -> dict:
    sid = sebi_id.strip().upper()
    ok = bool(SEBI_ID_RE.match(sid))
    return {"input": sid, "pattern_valid": ok}


def bulk_registry_check(identifiers: dict) -> dict:
    """
    identifiers = {"lei": "...", "isin": "...", "cin": "...", "sebi": "..."}
    """
    out = {}
    if "lei" in identifiers:
        out["lei"] = validate_lei(identifiers["lei"])
    if "isin" in identifiers:
        out["isin"] = validate_isin(identifiers["isin"])
    if "cin" in identifiers:
        out["cin"] = validate_cin(identifiers["cin"])
    if "sebi" in identifiers:
        out["sebi"] = validate_sebi_id(identifiers["sebi"])
    return out
