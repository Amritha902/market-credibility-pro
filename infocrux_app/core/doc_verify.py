from __future__ import annotations
import re, io, hashlib
from typing import Dict, Any, List, Tuple
from PyPDF2 import PdfReader

RISK_PHRASES = [
    "guaranteed returns", "assured returns", "firm allotment",
    "fast-track", "exclusive", "operator tip", "inside tip",
    "no risk", "unprecedented", "guaranteed", "assured"
]

DIN_RE = re.compile(r"\bDIN[:\- ]?([A-Z0-9]{6,})\b", re.I)
DATE_RE = re.compile(r"\b(\d{1,2}[\-/](\d{1,2}|[A-Za-z]{3,9})[\-/]\d{2,4})\b")
SEBI_RE = re.compile(r"\bSecurities and Exchange Board of India\b|\bSEBI\b", re.I)
FAKE_DEPT_RE = re.compile(r"\bDepartment of SEBI\b", re.I)

def sha256_bytes(b: bytes) -> str:
    import hashlib
    return "sha256:" + hashlib.sha256(b).hexdigest()

def extract_pdf_text(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        txt = "\n".join(pages)
        meta = {"pages": len(reader.pages), "encrypted": reader.is_encrypted}
        return txt, meta
    except Exception as e:
        return "", {"error": str(e)}

def score_document(text: str) -> Tuple[float, List[str], Dict[str, bool]]:
    txt = text.lower()
    reasons = []
    checks = {
        "has_sebi_name": bool(SEBI_RE.search(txt)),
        "has_din": bool(DIN_RE.search(txt)),
        "has_date": bool(DATE_RE.search(txt)),
        "has_risk_phrases": any(p in txt for p in RISK_PHRASES),
        "has_fake_dept": bool(FAKE_DEPT_RE.search(txt)),
    }
    score = 60.0
    if checks["has_sebi_name"]: score += 5
    if checks["has_din"]: score += 10
    if checks["has_date"]: score += 5
    if checks["has_risk_phrases"]:
        score -= 25; reasons.append("Contains promotional / risky phrases")
    if checks["has_fake_dept"]:
        score -= 20; reasons.append("Suspicious 'Department of SEBI' phrase")
    if not checks["has_din"]:
        reasons.append("Missing DIN / reference number")
    if not checks["has_date"]:
        reasons.append("Missing or malformed date")
    if not checks["has_sebi_name"]:
        reasons.append("SEBI name not present")
    score = max(0, min(100, score))
    return score, reasons, checks

def verify_pdf(file_bytes: bytes) -> Dict[str, Any]:
    text, meta = extract_pdf_text(file_bytes)
    doc_hash = sha256_bytes(file_bytes)
    score, reasons, checks = score_document(text)
    level = "Low" if score >= 70 else "Medium" if score >= 35 else "High"
    excerpt = text[:1000]
    return {
        "doc_hash": doc_hash,
        "meta": meta,
        "score": round(float(score),2),
        "level": level,
        "reasons": reasons,
        "checks": checks,
        "excerpt": excerpt,
    }
