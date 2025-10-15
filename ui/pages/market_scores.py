# ui/pages/market_scores.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# keep the same import style you’re using elsewhere
from ui.components.helpers import fetch_alpha_timeseries, compute_indicators

# --- paths to demo data (relative to project root) ---
PROJ_ROOT = Path(__file__).resolve().parents[2]
DEMO_MKT = PROJ_ROOT / "data" / "demo_market.csv"
DEMO_NEWS = PROJ_ROOT / "data" / "demo_announcements.csv"

def _load_demo_market(symbol: str | None = None) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(DEMO_MKT)
        # expected columns: date, symbol, close (plus optional open/high/low/volume)
        if symbol:
            df = df[df["symbol"].str.upper() == symbol.upper()].copy()
        # if no symbol filter or not found, just take first symbol’s series
        if df.empty:
            return None
        # ensure sorted and formatted
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        # if multiple symbols present, keep the last selected or first
        if symbol is None:
            first_sym = df["symbol"].iloc[0]
            df = df[df["symbol"] == first_sym].copy()
        # unify colnames used later
        if "close" not in df.columns:
            # fall back if the demo file has 'price' instead
            if "price" in df.columns:
                df = df.rename(columns={"price": "close"})
            else:
                return None
        return df.sort_values("date").reset_index(drop=True)
    except Exception:
        return None

def _load_demo_news(symbol_hint: str) -> pd.DataFrame | None:
    try:
        news = pd.read_csv(DEMO_NEWS)
        # expected columns: date, title, body (optional), symbols (optional)
        s = (symbol_hint or "").upper()
        if "symbols" in news.columns:
            mask = news["symbols"].fillna("").str.upper().str.contains(s)
            out = news[mask].copy()
        else:
            # fallback: simple keyword match in title/body
            mask = (
                news.get("title", pd.Series([""]*len(news))).fillna("").str.upper().str.contains(s) |
                news.get("body", pd.Series([""]*len(news))).fillna("").str.upper().str.contains(s)
            )
            out = news[mask].copy()
        return out.sort_values("date", ascending=False).head(10).reset_index(drop=True)
    except Exception:
        return None

def _portfolio_summary(df_prices: pd.DataFrame, portfolio: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Very lightweight P&L snapshot for one-symbol portfolio.
    portfolio columns expected: symbol, qty, avg_cost
    """
    if portfolio is None or portfolio.empty or df_prices is None or df_prices.empty:
        return None
    latest_close = float(df_prices["close"].iloc[-1])
    sym = portfolio["symbol"].iloc[0]
    qty = float(portfolio["qty"].iloc[0])
    avg = float(portfolio["avg_cost"].iloc[0])
    mv = qty * latest_close
    cost = qty * avg
    pl = mv - cost
    return pd.DataFrame([{
        "Symbol": sym,
        "Qty": qty,
        "Avg Cost": round(avg, 2),
        "Last Close": round(latest_close, 2),
        "Market Value": round(mv, 2),
        "P/L": round(pl, 2),
        "P/L %": round((pl / cost) * 100 if cost else np.nan, 2),
    }])

def _render_charts(df: pd.DataFrame):
    st.markdown("#### Price")
    st.line_chart(df.set_index("date")[["close"]], height=280)

    # daily returns histogram
    work = df.copy()
    work["ret"] = work["close"].pct_change()
    fig_h = px.histogram(
        work.dropna(), x="ret", nbins=40, title="Distribution of Daily Returns"
    )
    fig_h.update_layout(yaxis_title="Frequency", xaxis_title="Daily Return")
    st.plotly_chart(fig_h, use_container_width=True)

    # donut snapshot
    latest = df.iloc[-1]
    states = {
        "Above SMA20": int(latest.get("close", np.nan) > latest.get("SMA20", np.nan)),
        "Above SMA50": int(latest.get("close", np.nan) > latest.get("SMA50", np.nan)),
        "Above SMA200": int(latest.get("close", np.nan) > latest.get("SMA200", np.nan)),
        "RSI>70 (Overbought)": int(latest.get("RSI14", 0) > 70),
        "RSI<30 (Oversold)": int(latest.get("RSI14", 0) < 30),
        "MACD>Signal": int(latest.get("MACD", 0) > latest.get("MACDsig", 0)),
    }
    donut_df = pd.DataFrame({"Condition": list(states.keys()),
                             "Active": ["Yes" if v else "No" for v in states.values()],
                             "Value": [1]*len(states)})
    fig_d = px.pie(
        donut_df, names="Condition", values="Value", hole=0.55,
        title="Technical Snapshot (Latest Day)", color="Active",
        color_discrete_map={"Yes": "#2ecc71", "No": "#e74c3c"}
    )
    st.plotly_chart(fig_d, use_container_width=True)

    # risk table
    risk_rows = [
        {
            "Metric": "Price vs SMA200",
            "Status": "Above" if latest.get("close", 0) > latest.get("SMA200", 0) else "Below",
            "Risk": "Lower" if latest.get("close", 0) > latest.get("SMA200", 0) else "Higher"
        },
        {
            "Metric": "RSI (14d)",
            "Status": f"{latest.get('RSI14', np.nan):.1f}" if pd.notna(latest.get("RSI14", np.nan)) else "—",
            "Risk": "Overbought" if latest.get("RSI14", 0) > 70 else ("Oversold" if latest.get("RSI14", 0) < 30 else "Neutral")
        },
        {
            "Metric": "MACD-Hist",
            "Status": f"{latest.get('MACDhist', np.nan):.4f}" if pd.notna(latest.get("MACDhist", np.nan)) else "—",
            "Risk": "Bullish" if latest.get("MACDhist", 0) > 0 else "Bearish"
        }
    ]
    st.markdown("#### Risk Snapshot")
    st.dataframe(pd.DataFrame(risk_rows), use_container_width=True)

def render():
    st.subheader("📊 Market & Scores")

    # left: symbol + actions; right: portfolio uploader
    c1, c2 = st.columns([2, 1])
    with c1:
        symbol = st.text_input("Symbol (Alpha Vantage ticker)", value="RELIANCE.BSE")
        b_live, b_demo = st.columns(2)
        with b_live:
            go_live = st.button("Fetch Live", use_container_width=True)
        with b_demo:
            go_demo = st.button("Use Demo Data", use_container_width=True)

    with c2:
        st.caption("Optional portfolio upload (CSV: symbol,qty,avg_cost)")
        up = st.file_uploader("Portfolio CSV", type=["csv"], label_visibility="collapsed")
        portfolio_df = None
        if up:
            try:
                tmp = pd.read_csv(up)
                cols = [c.lower() for c in tmp.columns]
                colmap = {c: c.lower() for c in tmp.columns}
                tmp = tmp.rename(columns=colmap)
                if all(c in tmp.columns for c in ["symbol", "qty", "avg_cost"]):
                    # keep only the first row for this symbol (simple demo)
                    sel = tmp[tmp["symbol"].str.upper() == symbol.upper()]
                    portfolio_df = sel.head(1).copy() if not sel.empty else tmp.head(1).copy()
                else:
                    st.warning("Expected columns: symbol, qty, avg_cost")
            except Exception as e:
                st.error(f"Failed to read portfolio CSV: {e}")

    # no button yet? guide the user
    if not (go_live or go_demo):
        st.info("Enter a symbol (e.g., RELIANCE.BSE, TCS.BSE, INFY.BSE) and click **Fetch Live**. "
                "If API rate limits hit, click **Use Demo Data** to see a full walkthrough.")
        return

    # load price series
    if go_demo:
        df = _load_demo_market(symbol)
        demo_mode = True
        if df is None or df.empty:
            st.error("Demo market file missing or empty. Please ensure data/demo_market.csv is present.")
            return
    else:
        df = fetch_alpha_timeseries(symbol)
        demo_mode = False
        if df is None or df.empty:
            st.warning("No live data returned (API key/limit). Falling back to demo.")
            df = _load_demo_market(symbol)
            demo_mode = True
            if df is None or df.empty:
                st.error("Demo market file missing or empty. Please ensure data/demo_market.csv is present.")
                return

    # unify required columns
    if "date" not in df.columns or "close" not in df.columns:
        st.error("Dataframe missing required columns: date, close.")
        return

    # compute indicators and render
    df = compute_indicators(df)
    # brief P&L if portfolio provided
    ps = _portfolio_summary(df, portfolio_df)
    if ps is not None:
        st.markdown("#### Portfolio Snapshot")
        st.dataframe(ps, use_container_width=True)

    _render_charts(df)

    # related news (demo only; live news scraping would go elsewhere)
    if demo_mode:
        st.markdown("#### Related News (Demo)")
        news = _load_demo_news(symbol)
        if news is not None and not news.empty:
            st.dataframe(news[["date", "title"]], use_container_width=True, height=260)
        else:
            st.caption("No demo news found for this symbol in data/demo_announcements.csv.")

    # footer status
    st.caption(("Mode: DEMO (from data/demo_market.csv)" if demo_mode else "Mode: LIVE (Alpha Vantage)"))
