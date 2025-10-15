import requests

UA = {"User-Agent": "InfoCrux Jury Demo/1.0"}

def fetch(url: str, timeout: int = 20):
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception:
        return None

def verify_against_official_sources(text_or_title: str, company_hint: str = ""):
    # Placeholder lightweight heuristic; extend with official endpoints when available.
    # Always returns a dict with 'verdict', 'reason', 'links' keys.
    return {"verdict": "unverified", "reason": "No official match via lightweight search", "links": []}
