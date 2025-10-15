from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ui.components.helpers import fetch_alpha_timeseries, compute_indicators

PROJ_ROOT = Path(__file__).resolve().parents[2]
SECTOR_JSON = PROJ_ROOT / "data" / "sector_watchlist.json"
DEMO_MKT = PROJ_ROOT / "data" / "demo_market.csv"
DEMO_NEWS = PROJ_ROOT / "data" / "demo_announcements.csv"

NEG_WORDS = ["fraud", "ban", "probe", "penalty", "raid", "default", "warning", "scam", "halt", "suspension"]

# -------------------- helpers --------------------

def _load_sectors() -> dict:
    if SECTOR_JSON.exists():
        try:
            return json.loads(SECTOR_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    # sensible default if file missing
    return {
        "Pharma": ["SUNPHARMA.BSE", "DRREDDY.BSE"],
        "Telecom": ["BHARTIARTL.BSE", "IDEA.BSE"],
        "Energy": ["RELIANCE.BSE", "ONGC.BSE"],
    }

def _load_demo_market(symbols: list[str]) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(DEMO_MKT)
        # expected: date, symbol, close (others optional)
        df = df[df["symbol"].isin(symbols)].copy()
        if df.empty: 
            return None
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df.sort_values(["symbol", "date"]).reset_index(drop=True)
    except Exception:
        return None

def _load_demo_news(symbols: list[str]) -> pd.DataFrame | None:
    try:
        news = pd.read_csv(DEMO_NEWS)
        # try to filter by symbols column; else fallback to keyword in title/body
        if "symbols" in news.columns:
            mask = news["symbols"].fillna("").apply(lambda s: any(sym.upper() in s.upper() for sym in symbols))
            out = news[mask].copy()
        else:
            mask = news.get("title", pd.Series([""]*len(news))).fillna("").apply(
                lambda t: any(sym.split(".")[0] in t.upper() for sym in symbols)
            )
            out = news[mask].copy()
        return out.sort_values("date", ascending=False).reset_index(drop=True)
    except Exception:
        return None

def _symbol_metrics(symbol: str, demo_mode: bool) -> dict:
    # live first
    df = None if demo_mode else fetch_alpha_timeseries(symbol)
    if (df is None) or df.empty:
        # demo fallback
        ddf = _load_demo_market([symbol])
        if ddf is not None and not ddf.empty:
            df = ddf[ddf["symbol"] == symbol].copy()
            df = df.drop(columns=[c for c in ["symbol"] if c in df.columns])
    if df is None or df.empty:
        return {"symbol": symbol, "ok": False}

    df = compute_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    chg = (last["close"] - prev["close"]) / prev["close"] * 100 if prev["close"] else 0.0

    # risk score (0 good → 100 risky)
    risk = 0
    # below long-term trend => riskier
    if pd.notna(last.get("SMA200", np.nan)) and last["close"] < last["SMA200"]:
        risk += 35
    # momentum/overbought/oversold extremes
    rsi = float(last.get("RSI14", 50))
    if rsi > 70: risk += 20
    if rsi < 30: risk += 10
    # big 1d drop
    if chg < -2.0: risk += min(30, abs(chg))  # cap contribution

    return {
        "symbol": symbol,
        "ok": True,
        "last_close": float(last["close"]),
        "d1_change_%": float(round(chg, 2)),
        "RSI14": float(round(rsi, 1)),
        "above_SMA200": bool(pd.notna(last.get("SMA200", np.nan)) and last["close"] > last["SMA200"]),
        "risk_score": int(round(min(100, max(0, risk)))),
    }

def _portfolio_from_upload(file) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(file)
        # normalize headers
        df.columns = [c.strip().lower() for c in df.columns]
        if not set(["symbol", "qty", "avg_cost"]).issubset(df.columns):
            st.warning("Portfolio CSV must have columns: symbol, qty, avg_cost")
            return None
        return df
    except Exception as e:
        st.error(f"Failed to read portfolio CSV: {e}")
        return None

def _flag_negative_news(news_df: pd.DataFrame, symbol: str) -> bool:
    if news_df is None or news_df.empty:
        return False
    # very light heuristic
    col = "title" if "title" in news_df.columns else news_df.columns[0]
    rows = news_df[news_df[col].astype(str).str.contains(symbol.split(".")[0], case=False, na=False)]
    if rows.empty:
        return False
    text_block = " ".join(rows[col].astype(str).tolist()).lower()
    return any(w in text_block for w in NEG_WORDS)

# -------------------- page --------------------

def render():
    st.subheader("🧭 Sector Risk Dashboard")

    sectors = _load_sectors()
    left, right = st.columns([2, 1])

    with left:
        sector = st.selectbox("Choose sector", list(sectors.keys()))
        symbols = sectors.get(sector, [])
        live_col, demo_col = st.columns(2)
        with live_col:
            run_live = st.button("Fetch Live", use_container_width=True)
        with demo_col:
            run_demo = st.button("Use Demo Data", use_container_width=True)

    with right:
        st.caption("Optional: Upload your portfolio CSV (`symbol, qty, avg_cost`)")
        up = st.file_uploader("Upload", type=["csv"], label_visibility="collapsed")
        portfolio = _portfolio_from_upload(up) if up else None

    if not (run_live or run_demo):
        st.info("Select a sector and click **Fetch Live**. If rate limited, click **Use Demo Data**.")
        return

    demo_mode = bool(run_demo)

    # Pull metrics for each symbol
    rows = []
    for s in symbols:
        m = _symbol_metrics(s, demo_mode=demo_mode)
        # optionally add a news-flag (demo file)
        demo_news = _load_demo_news(symbols) if demo_mode else None
        m["news_flag"] = _flag_negative_news(demo_news, s) if demo_mode else False
        rows.append(m)

    df = pd.DataFrame(rows)
    if df.empty or not df["ok"].any():
        st.error("No data available for the selected sector/symbols.")
        return

    # annotate holdings
    df["holding"] = False
    if portfolio is not None and not portfolio.empty:
        hold_syms = set(portfolio["symbol"].astype(str).str.upper())
        df["holding"] = df["symbol"].astype(str).str.upper().isin(hold_syms)

    # summary tiles
    colA, colB, colC, colD = st.columns(4)
    with colA:
        st.metric("Symbols", int(df.shape[0]))
    with colB:
        st.metric("Avg Risk", int(df["risk_score"].mean()))
    with colC:
        st.metric("Rising vs SMA200", f"{int(df['above_SMA200'].sum())}/{df.shape[0]}")
    with colD:
        st.metric("Holdings at Risk", int(df[(df["holding"]) & (df["risk_score"] >= 60)].shape[0]))

    # styled table
    show_cols = ["symbol", "last_close", "d1_change_%", "RSI14", "above_SMA200", "risk_score", "holding", "news_flag"]
    table = df[show_cols].fillna("—").copy()
    st.dataframe(table, use_container_width=True, height=280)

    # heatmap (risk)
    heat = df[["symbol", "risk_score"]].copy()
    heat["risk_bucket"] = pd.cut(heat["risk_score"], bins=[-1, 30, 60, 100], labels=["Low", "Medium", "High"])
    fig = px.imshow(
        heat[["risk_score"]].T,
        color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
        aspect="auto",
        labels=dict(color="Risk"),
    )
    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(ticktext=heat["symbol"], tickvals=list(range(len(heat["symbol"]))), tickangle=45)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # at-risk holdings panel
    if portfolio is not None and not portfolio.empty:
        risky = df[(df["holding"]) & (df["risk_score"] >= 60)].sort_values("risk_score", ascending=False)
        st.markdown("### 🔴 At-Risk Holdings")
        if risky.empty:
            st.success("No holdings breach the risk threshold (>= 60).")
        else:
            st.dataframe(risky[["symbol", "risk_score", "d1_change_%", "RSI14", "above_SMA200", "news_flag"]], use_container_width=True)

    # footer
    st.caption("Mode: DEMO (file) ✅" if demo_mode else "Mode: LIVE (Alpha Vantage) 🌐")
