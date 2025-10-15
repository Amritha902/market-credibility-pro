# ui/pages/document_verifier.py
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st
# ---- JSON sanitizer (recursive) ----
def _json_safe(o):
    import numpy as np, pandas as pd, datetime as dt
    # scalars
    if isinstance(o, (np.integer,)):   return int(o)
    if isinstance(o, (np.floating,)):  return float(o)
    if isinstance(o, (np.bool_,)):     return bool(o)
    # pandas/np containers
    if isinstance(o, (pd.Timestamp,)): return o.isoformat()
    if isinstance(o, (np.ndarray,)):   return o.tolist()
    # datetime
    if isinstance(o, (dt.datetime, dt.date)): return o.isoformat()
    # bytes
    if isinstance(o, (bytes, bytearray)): return None
    # sets/tuples
    if isinstance(o, (set, tuple)):    return list(o)
    # fallback
    return str(o)

def _sanitize(obj):
    """Deep-convert any nested structure into JSON-safe primitives."""
    import numpy as np, pandas as pd, datetime as dt
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    # handle numpy/pandas scalars early
    try:
        return _json_safe(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return {str(k): _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize(x) for x in obj]
    # last resort
    return _json_safe(obj)


# ---- project helpers (your existing functions) ----
try:
    from ui.components.helpers import (
        parse_any_file,
        check_document_link,
        lookup_entity,
        verify_announcement,      # uses your scrapers + suggestions
        gemini_explain,           # grounded LLM explanation
        save_evidence,            # Supabase insert
    )
except Exception:
    from components.helpers import (
        parse_any_file,
        check_document_link,
        lookup_entity,
        verify_announcement,
        gemini_explain,
        save_evidence,
    )

# ---- optional core modules (best-effort; page works even if they’re missing) ----
try:
    from core.registry_checks import bulk_registry_check
except Exception:
    bulk_registry_check = None

try:
    from core.social_signals import SocialSignalClassifier
except Exception:
    SocialSignalClassifier = None

try:
    from core.anomaly_detector import AnomalyDetector
except Exception:
    AnomalyDetector = None

try:
    from core.market_contra import contradiction_score
except Exception:
    contradiction_score = None


# ---------- identifier regex (fast, no heavy deps) ----------
LEI_RE  = re.compile(r"\b[A-Z0-9]{18}[0-9]{2}\b", re.I)
ISIN_RE = re.compile(r"\b[A-Z]{2}[A-Z0-9]{9}[0-9]\b", re.I)
CIN_RE  = re.compile(r"\b[LUAP][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b", re.I)
SEBI_RE = re.compile(r"\b[0-9A-Z\-]{4,20}\b", re.I)

def extract_identifiers(text: str) -> Dict[str, str]:
    ids: Dict[str, str] = {}
    if not text:
        return ids
    lei = LEI_RE.search(text)
    isin = ISIN_RE.search(text)
    cin = CIN_RE.search(text)
    # SEBI id: only capture when annotated to avoid random tokens
    sebi = re.search(r"\b(SEBI|REG|REGN|REGISTRATION)\s*:?[\s\-]*([0-9A-Z\-]{4,20})", text, re.I)

    if lei:  ids["lei"]  = lei.group(0).upper()
    if isin: ids["isin"] = isin.group(0).upper()
    if cin:  ids["cin"]  = cin.group(0).upper()
    if sebi: ids["sebi"] = sebi.group(2).upper()
    return ids


# ---------- scoring ----------
def score_from_signals(signals: Dict[str, Any]) -> (int, pd.DataFrame):
    """
    Turn all signals into a 0–100 credibility score with a breakdown DataFrame.
    Positive = more credible; negative = risky.
    """
    rows = []

    # start neutral
    base = 50
    rows.append(("Baseline", +50, "Neutral baseline"))

    # lookup
    if signals.get("lookup", {}).get("found"):
        rows.append(("Local Registry Match", +20, "Found in data/lookup.json"))
    else:
        rows.append(("Local Registry Match", +0, "No curated match"))

    # official/scraper
    off = signals.get("official", {}) or {}
    if off.get("verdict") == "verified":
        rows.append(("Official Filing Match", +30, "Matched regulator/exchange via scraper"))
    elif off.get("verdict") == "needs_official_link":
        rows.append(("Regulator Suggested", +5, "No exact match but regulators suggested"))
    else:
        rows.append(("Official Filing Match", -5, "Not found in official sources (light check)"))

    # url hygiene
    url_sig = signals.get("url", {}) or {}
    if url_sig.get("verdict") == "likely-official":
        rows.append(("URL Domain Official-ish", +10, "Domain looks official (e.g., sebi/nse/bse/gleif/fda/cdsco)"))
    elif url_sig.get("verdict") == "risky":
        rows.append(("URL Risk (VirusTotal)", -40, "Malicious indicators on domain"))
    elif url_sig:
        rows.append(("URL Scan Presence", +2, "URL was scanned / reachable"))

    # identifiers validation
    id_sig = signals.get("identifiers", {}) or {}
    if id_sig:
        ok = []
        for k, v in id_sig.items():
            if isinstance(v, dict) and v.get("pattern_valid"):
                ok.append(k.upper())
        if ok:
            rows.append(("Identifiers Valid", +10, f"Valid pattern(s): {', '.join(ok)}"))

    # extracted text presence
    if signals.get("text_len", 0) > 40:
        rows.append(("Text Extracted", +5, "OCR/Text extracted successfully"))
    else:
        rows.append(("Text Extracted", -3, "No/low extractable text"))

    # social signal (optional)
    soc = signals.get("social", {}) or {}
    if soc.get("label") == "legit":
        rows.append(("Social Signal", +5, "Classified as legit"))
    elif soc:
        rows.append(("Social Signal", -5, "Classified as suspicious"))

    # anomaly (optional)
    anom = signals.get("anomaly", {}) or {}
    if anom.get("any"):
        rows.append(("Numeric Anomaly", -12, "Outlier vs history (demo rule)"))

    # market contradiction (optional)
    contra = signals.get("contra", {}) or {}
    if contra.get("contradiction_score", 0) >= 2:
        rows.append(("Market Contradiction", -8, "Price/RSI contradicts positive claim"))

    # clamp and return
    total = sum(v for _, v, _ in rows)
    total = max(0, min(100, total))
    df = pd.DataFrame(rows, columns=["Dimension", "Contribution", "Why"])
    return total, df

# put near the top of document_verifier.py (after imports)


# ---------- page ----------
def render():
    st.subheader("🛡️ Document Verifier — URL / File / Media / Text")
    st.caption("We parse content (OCR/STT), validate identifiers, check official sources & domain hygiene, "
               "classify language, and combine them into a single credibility score with a transparent breakdown.")

    left, right = st.columns([2, 1])

    with left:
        url = st.text_input("URL (official IR / exchange / regulator preferred)")
        file = st.file_uploader("Upload (PDF, DOCX, PPTX, PNG, JPG, JPEG, MP3, WAV, MP4, MOV)", accept_multiple_files=False)
        text = st.text_area("Or paste raw text / announcement")

        c1, c2, c3 = st.columns(3)
        run = c1.button("Analyze (Live)")
        demo_pdf = c2.button("Use Demo PDF")
        demo_link = c3.button("Use Demo Link")

    with right:
        st.markdown("**Tips**")
        st.markdown("- Provide **either** a URL, or upload a file, or paste text.\n"
                    "- For scanned images, OCR is used. For audio/video, speech-to-text (when libs available).")

    # Demo helpers
    if demo_link:
        url = "https://www.sebi.gov.in/"
        run = True
    demo_bytes = None
    if demo_pdf:
        p = Path(__file__).resolve().parents[2] / "data" / "demo_document.pdf"
        if p.exists():
            demo_bytes = p.read_bytes()
            run = True
        else:
            st.warning("Missing data/demo_document.pdf")

    if not run:
        st.info("Paste a URL or upload a file (or use a demo) and click **Analyze (Live)**.")
        return

    # ---------- 1) Parse file / collect text ----------
    extracted_text = ""
    upload_meta = {}
    try:
        if file is not None:
            parsed = parse_any_file(file)           # your helper (PDF/DOCX/PPTX/Image OCR)
            extracted_text = parsed.get("text", "") or ""
            upload_meta = {"name": parsed.get("name")}
        elif demo_bytes is not None:
            # mimic UploadedFile for parse_any_file
            dummy = type("U", (), {"name": "demo_document.pdf", "read": lambda: demo_bytes})
            parsed = parse_any_file(dummy)
            extracted_text = parsed.get("text", "") or ""
            upload_meta = {"name": "demo_document.pdf"}
    except Exception as e:
        st.error(f"File parse failed: {e}")

    # Combine with manual text area for fuller context
    combined_text = ((text or "") + "\n" + (extracted_text or "")).strip()

    # ---------- 2) Local lookup ----------
    lookup = lookup_entity((combined_text + " " + (url or "")).strip())

    # ---------- 3) URL hygiene ----------
    url_hyg = check_document_link(url) if url else {}

    # ---------- 4) Official/regulator check ----------
    off = verify_announcement((combined_text or url or "")[:400], link=url or "")

    # ---------- 5) Identifiers (regex) + registry validation ----------
    ids = extract_identifiers(combined_text)
    reg = {}
    if ids and bulk_registry_check:
        try:
            reg = bulk_registry_check(ids)
        except Exception as e:
            reg = {"error": f"registry check failed: {e}"}

    # ---------- 6) Optional: social / anomaly / contradiction ----------
    social = {}
    if SocialSignalClassifier and combined_text:
        try:
            social = SocialSignalClassifier().classify(combined_text)
        except Exception:
            pass

    anomaly = {}
    if AnomalyDetector:
        try:
            # demo: compare a fabricated filing vs tiny history
            hist = [{"revenue": 100, "profit": 18}, {"revenue": 104, "profit": 20}]
            anomaly = AnomalyDetector().compare_filing({"revenue": 150, "profit": 9}, hist)
            anomaly["any"] = any(v.get("anomaly") for v in anomaly.values()) if isinstance(anomaly, dict) else False
        except Exception:
            pass

    contra = {}
    if contradiction_score:
        try:
            prices = [100, 102, 101, 99, 97, 96, 95, 94, 93, 92]  # demo series; replace with live when wired
            contra = contradiction_score(prices, "positive")
        except Exception:
            pass

    # ---------- 7) Score ----------
    signals = {
        "lookup": lookup,
        "url": url_hyg,
        "official": off,
        "identifiers": reg,
        "text_len": len(combined_text),
        "social": social,
        "anomaly": anomaly,
        "contra": contra,
    }
    score, breakdown = score_from_signals(signals)

    # ---------- 8) Gemini explanation (grounded) ----------
    try:
        refs = []
        if lookup.get("found") and lookup.get("official_sites"):
            refs += lookup["official_sites"]
        off_official = off.get("evidence", {}).get("official", {}) if isinstance(off, dict) else {}
        refs += off_official.get("references", []) if isinstance(off_official, dict) else []
        expl = gemini_explain({
            "claim": (combined_text or url or "")[:2000],
            "verdict_text": f"Credibility score: {score}/100",
            "lookup": lookup if lookup.get("found") else None,
            "reasons": breakdown.sort_values("Contribution", ascending=False)["Why"].tolist()[:6],
            "references": refs[:6],
        })
    except Exception:
        expl = "AI explanation unavailable."

    # ---------- 9) Render ----------
    st.markdown("## ✅ Verdict")
    st.metric("Credibility Score (0 risky → 100 credible)", f"{score}/100")

    st.markdown("### 📊 Score Breakdown")
    st.dataframe(breakdown, use_container_width=True)

    st.markdown("### 🔎 Signals")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Local Lookup**")
        st.json(lookup or {})
        st.markdown("**Identifiers (regex + registry)**")
        st.json({"found": ids, "registry": reg} if ids else {"found": {}, "registry": reg})
        st.markdown("**Official / Scraper Result**")
        st.json(off or {})
    with colB:
        st.markdown("**URL Hygiene**")
        st.json(url_hyg or {})
        if social:
            st.markdown("**Social Signal**")
            st.json(social)
        if anomaly:
            st.markdown("**Anomaly Check**")
            st.json(anomaly)
        if contra:
            st.markdown("**Market Contradiction**")
            st.json(contra)

    st.markdown("### 🤖 AI Explanation")
    st.write(expl)

    # ---------- 10) Save / Download ----------
    evidence = {
        "ts": int(time.time()),
        "url": url,
        "upload_meta": upload_meta,
        "lookup": lookup,
        "url_hygiene": url_hyg,
        "official": off,
        "identifiers": {"text_found": ids, "registry": reg},
        "social": social,
        "anomaly": anomaly,
        "contra": contra,
        "score": score,
        "breakdown": breakdown.to_dict(orient="records"),
        "text_snippet": (combined_text or "")[:800],
        "ai_explanation": expl,
    }
    st.download_button("⬇️ Download Evidence JSON", data=json.dumps(evidence, ensure_ascii=False, indent=2),
                       file_name="evidence.json", mime="application/json")

    if st.button("💾 Save to Evidence Vault (Supabase)"):
        res = save_evidence(evidence)
        if isinstance(res, dict) and res.get("error"):
            st.error(f"Not saved: {res['error']}")
        else:
            st.success("Saved to Evidence Vault.")
