# ui/pages/pump_group.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ---- Use your helpers (live APIs + demo fallback) ----
from ui.components.helpers import (
    fetch_alpha_timeseries,
    compute_indicators,
    advisor_entity_check,      # uses core.verifiers under the hood
)

# ---- Try to use your core fraud helpers; fall back if missing ----
try:
    from core.fraud_detection import tip_verdict, contradiction_score, SocialSignalClassifier
except Exception:
    def tip_verdict(text: str, ta_contradiction: bool = False) -> Dict[str, Any]:
        t = (text or "").lower()
        hype_kw = ["sure shot", "guaranteed", "multibagger", "100% return", "free tips", "pump"]
        suspicious = any(k in t for k in hype_kw)
        base = 60 if suspicious else 35
        if ta_contradiction:
            base = min(95, base + 25)
        label = "High Risk" if base >= 70 else ("Medium Risk" if base >= 45 else "Low Risk")
        return {"score": base, "label": label, "reasons": ["Heuristic hype/claims", "TA contradiction" if ta_contradiction else None]}

    def contradiction_score(prices, announcement_type: str = "positive"):
        prices = list(prices or [])
        if len(prices) < 20:
            return {"ma20": float(np.mean(prices)) if prices else np.nan, "rsi": 50.0, "contradiction_score": 0}
        ma20 = float(pd.Series(prices).rolling(20).mean().iloc[-1])
        # very light RSI approx
        deltas = np.diff(prices)
        up = np.clip(deltas, 0, None)
        down = -np.clip(deltas, None, 0)
        roll_up = pd.Series(up).rolling(14).mean().iloc[-1]
        roll_down = pd.Series(down).rolling(14).mean().iloc[-1] + 1e-9
        rs = roll_up / roll_down
        rsi = 100. - (100. / (1. + rs))
        last_price = prices[-1]
        score = 0
        if announcement_type == "positive" and last_price < ma20:
            score += 1
        if announcement_type == "negative" and last_price > ma20:
            score += 1
        if (rsi > 70 and announcement_type == "positive") or (rsi < 30 and announcement_type == "negative"):
            score += 1
        return {"ma20": ma20, "rsi": float(rsi), "contradiction_score": int(score)}

    class SocialSignalClassifier:
        def __init__(self):
            self.pos = {"confirmed", "filing", "regulatory", "results announced", "board meeting", "exchange"}
            self.neg = {"pump", "dm for tips", "multi-bagger", "target hit", "join group", "sure shot", "insider"}

        def classify(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
            t = (text or "").lower()
            score = 0.5
            if any(k in t for k in self.pos): score += 0.25
            if any(k in t for k in self.neg): score -= 0.35
            score = float(max(0.0, min(1.0, score)))
            return {"text": text, "score": score, "label": "legit" if score >= threshold else "suspicious"}

# ---- Demo data paths ----
PROJ_ROOT = Path(__file__).resolve().parents[2]
DEMO_MKT = PROJ_ROOT / "data" / "demo_market.csv"

# ---- Small helpers ----
def _load_demo_market(symbol: str | None = None) -> Optional[pd.DataFrame]:
    try:
        df = pd.read_csv(DEMO_MKT)
        # expected cols: date, symbol, close (open/high/low/volume optional)
        if symbol:
            df = df[df["symbol"].str.upper() == symbol.upper()].copy()
        if df.empty:
            return None
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        if "close" not in df.columns:
            if "price" in df.columns:
                df = df.rename(columns={"price": "close"})
            else:
                return None
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None

def _parse_identifiers(raw: str) -> Dict[str, str]:
    """
    Parse "LEI=..., ISIN=..., CIN=..., SEBI=..." style input.
    Accepts loose commas/spaces.
    """
    out = {}
    if not raw:
        return out
    parts = re.split(r"[,\n]+", raw)
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out

def _announcement_tone(text: str) -> str:
    t = (text or "").lower()
    pos_kw = ["buy", "upgrade", "approved", "acquisition", "results beat", "bonus", "dividend", "green"]
    neg_kw = ["sell", "downgrade", "default", "loss", "penalty", "delay", "fraud", "red"]
    if any(k in t for k in pos_kw): return "positive"
    if any(k in t for k in neg_kw): return "negative"
    return "neutral"

def _overall_score(*scores: int) -> int:
    # aggregate capped at 95; simple weighted mean for now
    vals = [s for s in scores if s is not None]
    if not vals:
        return 0
    return int(min(95, round(sum(vals) / len(vals))))

# ---- UI Page ----
def render():
    st.subheader("💬 Pump/Group Risk Analyzer")

    tip = st.text_area("Paste a tip / message", height=120, placeholder="e.g., 'BUY RELIANCE now, target 10% today. Sure shot!'")
    c1, c2 = st.columns([2, 1])
    with c1:
        symbol = st.text_input("Symbol to cross-check (optional)", value="RELIANCE.BSE")
    with c2:
        ident_raw = st.text_input("Optional identifiers (comma separated, e.g. LEI=..., ISIN=..., CIN=..., SEBI=...)")

    b1, b2 = st.columns(2)
    with b1:
        run_live = st.button("Analyze (Live)", use_container_width=True)
    with b2:
        run_demo = st.button("Analyze (Demo Data)", use_container_width=True)

    if not (run_live or run_demo):
        st.info("Paste a tip/message, optionally add a symbol & identifiers, then choose **Analyze (Live)** or **Analyze (Demo Data)**.")
        return

    # ---- Registry / Identifier checks ----
    st.markdown("### 1) Registry / Identifier Checks")
    identifiers = _parse_identifiers(ident_raw)
    if identifiers:
        reg = advisor_entity_check(next(iter(identifiers.values())))
        # advisor_entity_check validates format + optional LEI lookup;
        # for multiple, we also render simple pattern validation:
        extra = {}
        from core.verifiers import valid_isin, valid_lei, valid_cin, valid_sebi_id, lei_lookup
        if "lei" in identifiers:   extra["LEI"]  = {"value": identifiers["lei"],  "valid": bool(valid_lei(identifiers["lei"])),  "data": lei_lookup(identifiers["lei"])}
        if "isin" in identifiers:  extra["ISIN"] = {"value": identifiers["isin"], "valid": bool(valid_isin(identifiers["isin"]))}
        if "cin" in identifiers:   extra["CIN"]  = {"value": identifiers["cin"],  "valid": bool(valid_cin(identifiers["cin"]))}
        if "sebi" in identifiers:  extra["SEBI"] = {"value": identifiers["sebi"], "valid": bool(valid_sebi_id(identifiers["sebi"]))}
        st.json({"advisor_entity_check": reg, "extra_checks": extra})
    else:
        st.caption("No identifiers provided.")

    # ---- Price series + indicators ----
    st.markdown("### 2) Market Context (TA)")

    if run_demo:
        df = _load_demo_market(symbol)
        demo_mode = True
        if df is None or df.empty:
            st.error("Demo market file missing or empty. Please ensure data/demo_market.csv is present.")
            return
    else:
        df = fetch_alpha_timeseries(symbol) if symbol else None
        demo_mode = False
        if df is None or df.empty:
            st.warning("No live data returned (API key / rate limit). Falling back to demo.")
            df = _load_demo_market(symbol)
            demo_mode = True
            if df is None or df.empty:
                st.error("Demo market file missing or empty. Please ensure data/demo_market.csv is present.")
                return

    # compute indicators
    df = compute_indicators(df)

    # charts
    colp, colt = st.columns([2, 1])
    with colp:
        st.line_chart(df.set_index("date")[["close"]], height=280)
    with colt:
        latest = df.iloc[-1]
        st.metric("Close (latest)", f"{latest['close']:.2f}")
        st.metric("RSI(14)", f"{latest.get('RSI14', np.nan):.1f}")
        st.metric("MACD Hist", f"{latest.get('MACDhist', np.nan):.4f}")
        st.caption("Mode: DEMO" if demo_mode else "Mode: LIVE")

    # ---- TA contradiction vs message tone ----
    st.markdown("### 3) TA Contradiction vs Message Tone")
    tone = _announcement_tone(tip)
    contr = contradiction_score(df["close"].tolist(), announcement_type=tone if tone != "neutral" else "positive")
    st.write(f"Detected tone: **{tone}**")
    st.json(contr)

    # ---- Social signal classifier ----
    st.markdown("### 4) Social Signal Classification")
    clf = SocialSignalClassifier()
    sres = clf.classify(tip)
    st.json(sres)

    # ---- Heuristic pump verdict (hype + TA contradiction) ----
    st.markdown("### 5) Pump/Group Verdict")
    ta_contra_flag = bool(contr.get("contradiction_score", 0) >= 1)
    tvr = tip_verdict(tip, ta_contra_flag)
    st.write(f"**Pump/Group risk score:** {tvr['score']} — **{tvr['label']}**")
    if tvr.get("reasons"):
        st.write("Reasons:")
        for r in [x for x in tvr["reasons"] if x]:
            st.write(f"- {r}")

    # ---- Light anomaly scan on returns (z-score spikes) ----
    st.markdown("### 6) Return Spike Anomalies (Simple)")
    work = df.copy()
    work["ret"] = work["close"].pct_change()
    work["z"] = (work["ret"] - work["ret"].mean()) / (work["ret"].std() + 1e-9)
    spikes = work[work["z"].abs() > 3.0].tail(10)[["date", "ret", "z"]]
    if spikes.empty:
        st.caption("No extreme return spikes detected (|z| > 3).")
    else:
        st.dataframe(spikes, use_container_width=True)

    # histogram of returns
    fig_h = px.histogram(work.dropna(), x="ret", nbins=40, title="Distribution of Daily Returns")
    fig_h.update_layout(yaxis_title="Frequency", xaxis_title="Daily Return")
    st.plotly_chart(fig_h, use_container_width=True)

    # ---- Overall roll-up score ----
    st.markdown("### 7) Overall Roll-up")
    # Map classifier score (0..1) to 0..100
    social_score = int(round(sres["score"] * 100))
    contra_penalty = 15 if ta_contra_flag else 0
    overall = _overall_score(tvr["score"], social_score) + ( - contra_penalty )
    overall = int(max(0, min(95, overall)))
    overall_label = "High Risk" if overall >= 70 else ("Medium Risk" if overall >= 45 else "Low Risk")
    st.success(f"**Overall Pump/Group Risk:** {overall} — {overall_label}")

    st.caption("Notes: Heuristic-only demo. For production, wire richer social clustering, entity graph, and filing-aware anomaly models.")
