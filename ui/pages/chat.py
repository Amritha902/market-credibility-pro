# ui/pages/chat.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
import os
import streamlit as st

# --- Project helpers ---
try:
    from ui.components.helpers import (
        lookup_entity,
        verify_announcement,
        check_document_link,
        gemini_explain,
        save_evidence,
    )
except Exception:
    from components.helpers import (
        lookup_entity,
        verify_announcement,
        check_document_link,
        gemini_explain,
        save_evidence,
    )

# --- CrewAI orchestrator ---
CREW_OK = False
run_crew = None
try:
    from crewai_layer.orchestrator import run_credibility_crew as run_crew
    CREW_OK = callable(run_crew)
except Exception:
    CREW_OK = False
    run_crew = None

# --- Local JSON history ---
PROJ_ROOT = Path(__file__).resolve().parents[2]
HISTORY_JSON = PROJ_ROOT / "data" / "entity_history.json"

# --- API key check ---
missing_keys = []
if not os.getenv("OPENAI_API_KEY"): missing_keys.append("OPENAI_API_KEY")
if not os.getenv("GEMINI_API_KEY"): missing_keys.append("GEMINI_API_KEY")
if missing_keys:
    st.warning(f"⚠️ Missing API keys: {', '.join(missing_keys)}")


def _load_json(path: Path) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _json_safe(obj):
    import numpy as np, pandas as pd, datetime as dt
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, (np.bool_,)): return bool(obj)
    if isinstance(obj, (pd.Timestamp,)): return obj.isoformat()
    if isinstance(obj, (dt.date, dt.datetime)): return obj.isoformat()
    if isinstance(obj, (list, tuple, set)): return [_json_safe(x) for x in obj]
    if isinstance(obj, dict): return {str(k): _json_safe(v) for k, v in obj.items()}
    return str(obj)


# ---------- Render detailed block ----------
def _render_answer_block(res: Dict[str, Any]):
    st.markdown(f"### ✅ Verdict: **{res.get('verdict_text','unknown')}**")

    # What I checked
    st.markdown("**What I checked**")
    for c in res.get("what_i_checked", []):
        st.markdown(f"- {c}")
    if not res.get("what_i_checked"):
        st.markdown("- Local registry + official exchange scrapers + CrewAI agents")

    # Entity info
    if res.get("entity_info"):
        with st.expander("🏢 Entity & Registry Info"):
            st.json(res["entity_info"])

    # Confirmed / Silent
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Confirmed by (official)**")
        if res.get("who_confirmed"):
            for u in res["who_confirmed"]:
                st.markdown(f"- {u}")
        else:
            st.caption("— no regulator confirmed yet.")
    with cols[1]:
        st.markdown("**Silent / Not found (yet)**")
        if res.get("who_silent"):
            for s in res["who_silent"]:
                st.markdown(f"- {s}")
        else:
            st.caption("— none recorded.")

    # History
    with st.expander("⚖️ Prior adjudicated flags / patterns"):
        if res.get("history_flags"):
            st.json(res["history_flags"])
        else:
            st.caption("No prior history flags.")

    # Reasons
    if res.get("reasons"):
        st.markdown("**Reasons**")
        for r in res["reasons"]:
            st.markdown(f"- {r}")

    # References
    if res.get("references"):
        st.markdown("**References**")
        for ref in res["references"]:
            st.markdown(f"- {ref}")

    # Guidance
    if res.get("guidance"):
        st.markdown("### 🧭 What this means for you")
        for g in res["guidance"]:
            st.markdown(f"- {g}")

    # AI explanation
    if res.get("ai"):
        st.markdown("### 🤖 AI Explanation (grounded)")
        st.write(res["ai"])


# ---------- Core analysis ----------
def _analyze_claim(q: str) -> Dict[str, Any]:
    out = {
        "query": q,
        "verdict_text": "unknown",
        "reasons": [],
        "references": [],
        "entity_info": {},
        "who_confirmed": [],
        "who_silent": [],
        "history_flags": {},
        "guidance": [],
        "ai": "",
        "evidence": {},
        "what_i_checked": [],
        "crew_used": False,
    }

    strict_mode = True

    # Step 1: entity resolver always
    lookup = lookup_entity(q)
    if lookup.get("found"): out["entity_info"] = lookup

    # Step 2: baseline verification
    if q.strip().startswith(("http://", "https://")):
        out["what_i_checked"].append("Checked link hygiene (domain, VT/URLScan).")
        verify = check_document_link(q)
    else:
        out["what_i_checked"].append("Searched official exchanges/regulators via scraper.")
        verify = verify_announcement(q)

    out["verdict_text"] = verify.get("verdict", "unknown")
    out["reasons"] = (
        verify.get("official", {}).get("reasons", [])
        or ([verify.get("reason")] if verify.get("reason") else [])
        or verify.get("reasons", [])
    )
    out["references"] = (
        verify.get("official", {}).get("references", [])
        or verify.get("references", [])
    )
    out["evidence"] = verify.get("evidence", {})

    # Step 3: CrewAI deep sweep
    crew_payload = None
    if CREW_OK:
        try:
            out["what_i_checked"].append("CrewAI sweep (registries + news + filings + forensics).")
            crew_payload = run_crew(claim=q, lookup=lookup if lookup.get("found") else None, strict=strict_mode)
            out["crew_used"] = True
            if isinstance(crew_payload, dict):
                out["references"] = list(dict.fromkeys(out["references"] + crew_payload.get("references", [])))
                out["who_confirmed"] = list(dict.fromkeys(out["who_confirmed"] + crew_payload.get("confirmed_by", [])))
                out["who_silent"] = list(dict.fromkeys(out["who_silent"] + crew_payload.get("silent_or_missing", [])))
                if crew_payload.get("verdict_text"):
                    out["verdict_text"] = crew_payload["verdict_text"]
                out["reasons"] = list(dict.fromkeys(out["reasons"] + crew_payload.get("reasons", [])))
                if crew_payload.get("entity_info") and not out["entity_info"]:
                    out["entity_info"] = crew_payload["entity_info"]
        except Exception as e:
            out["what_i_checked"].append(f"CrewAI failed: {e}")

    # Step 4: confirmed/silent defaults
    if not out["who_confirmed"] and out["references"]:
        officialish = ["sebi", "nseindia", "bseindia", "gleif", "fda.gov", "cdsco", "mca.gov"]
        out["who_confirmed"] = [u for u in out["references"] if any(k in u for k in officialish)]
    if not out["who_silent"]:
        baseline = ["https://www.sebi.gov.in/", "https://www.nseindia.com/", "https://www.bseindia.com/"]
        out["who_silent"] = [u for u in baseline if u not in out["who_confirmed"]]

    # Step 5: history
    hist = _load_json(HISTORY_JSON) or {}
    if lookup.get("found") and lookup.get("entity") in hist:
        out["history_flags"] = hist[lookup["entity"]]

    # Step 6: guidance
    vt = out["verdict_text"].lower()
    if vt == "verified":
        out["guidance"] = [
            "✅ Officially confirmed. Review the full circular carefully.",
            "Check timing and materiality before acting.",
        ]
    elif vt == "unverified":
        out["guidance"] = [
            "⚠️ Treat this as unverified until exchange/regulator confirms.",
            "Avoid trading on screenshots or forwards.",
        ]
    else:
        out["guidance"] = ["Mixed/unclear signals. Wait for further confirmation."]

    # Step 7: AI explanation
    try:
        out["ai"] = gemini_explain({
            "claim": q,
            "lookup": lookup if lookup.get("found") else None,
            "verdict_text": out["verdict_text"],
            "reasons": out["reasons"],
            "references": out["references"],
        })
    except Exception:
        out["ai"] = ""

    # Step 8: evidence JSON
    out["evidence"] = _json_safe({
        "query": q,
        "verdict": out["verdict_text"],
        "reasons": out["reasons"],
        "references": out["references"],
        "entity": lookup if lookup.get("found") else {},
        "who_confirmed": out["who_confirmed"],
        "who_silent": out["who_silent"],
        "history_flags": out["history_flags"],
        "crew_used": out["crew_used"],
        "crew_payload": crew_payload or {},
    })
    return out


# ---------- Page ----------
def render():
    st.subheader("💬 Chat — Ask InfoCrux")
    st.caption("Forward a claim/tip/link and get a verdict with references. **Always strict + CrewAI enabled.**")

    if "chat" not in st.session_state:
        st.session_state.chat: List[Dict[str, Any]] = []

    # Input box (Enter sends)
    def _send_message():
        q = st.session_state.chat_prompt.strip()
        if q:
            result = _analyze_claim(q)
            st.session_state.chat.append(result)
            st.session_state.chat_prompt = ""

    st.text_input(
        "Type your question or paste a link/claim",
        key="chat_prompt",
        on_change=_send_message,
    )

    # Utility row
    u1, u2 = st.columns([1, 1])
    with u1:
        if st.button("🧹 Clear chat"):
            st.session_state.chat = []
    with u2:
        if st.button("💾 Save last to Evidence") and st.session_state.chat:
            res = save_evidence(st.session_state.chat[-1]["evidence"])
            if isinstance(res, dict) and res.get("ok"):
                st.success("Saved to Supabase.")
            else:
                st.warning("Save failed (check Supabase config).")

    # History
    st.markdown("### 📜 Chat History")
    if not st.session_state.chat:
        st.info("Try: `BSE Limited informs Exchange about Schedule of Meeting` or paste an NSE link.")
        return

    for item in reversed(st.session_state.chat):
        st.markdown(f"**You:** {item.get('query','')}")
        _render_answer_block(item)

        # Debug expander
        with st.expander("🔎 Debug: raw payloads"):
            st.json({
                "entity_info": item.get("entity_info", {}),
                "evidence": item.get("evidence", {}),
                "crew_used": item.get("crew_used", False),
            })

        # Download evidence
        st.download_button(
            "⬇️ Download Evidence JSON",
            data=json.dumps(item.get("evidence", {}), ensure_ascii=False, indent=2),
            file_name="chat_evidence.json",
            mime="application/json",
        )
        st.markdown("---")
