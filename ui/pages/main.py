# ui/pages/home.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# ---- helpers ----
try:
    from ui.components.helpers import fetch_alpha_timeseries, compute_indicators
except Exception:
    from components.helpers import fetch_alpha_timeseries, compute_indicators

# ---- paths ----
PROJ_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJ_ROOT / "data"
SECTOR_JSON = DATA_DIR / "sector_watchlist.json"
MKT_JSON = DATA_DIR / "market.json"
ANN_JSON = DATA_DIR / "announcements.json"
NEWS_JSON = DATA_DIR / "news.json"
PORTFOLIO_JSON = DATA_DIR / "portfolio.json"

# ---- loaders ----
def _load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _portfolio_df() -> pd.DataFrame | None:
    pf = _load_json(PORTFOLIO_JSON)
    if not pf:
        return None
    return pd.DataFrame(pf)

def _risk_badge(score: float) -> str:
    if score >= 70:
        return "🔴 High"
    elif score >= 40:
        return "🟠 Medium"
    return "🟢 Low"

# ---- page ----
def render():
    st.title("🏠 Home — Personalized Market Dashboard")
    st.caption("Live overview of your portfolio, market risks, announcements & news.")

    # --- Load data ---
    sectors = _load_json(SECTOR_JSON)
    mkt = _load_json(MKT_JSON)
    anns = _load_json(ANN_JSON)
    news = _load_json(NEWS_JSON)
    pf = _portfolio_df()

    # --- Portfolio Section ---
    st.markdown("## 💼 Portfolio Overview")

    total_val, risky_count, avg_risk = 0, 0, 0
    rows = []

    if pf is not None and not pf.empty:
        for _, row in pf.iterrows():
            sym = row["symbol"]
            qty = row["qty"]
            cost = row["avg_cost"]
            prices = [d["close"] for d in mkt.get(sym, [])][-200:] if mkt else []
            if prices:
                last_price = prices[-1]
                val = qty * last_price
                pl = (last_price - cost) * qty
                risk = np.random.randint(20, 90)  # placeholder risk; replace with real indicators
                total_val += val
                avg_risk += risk
                if risk >= 60:
                    risky_count += 1
                rows.append({
                    "symbol": sym,
                    "value": round(val, 2),
                    "risk_score": risk,
                    "pnl": round(pl, 2)
                })

        if rows:
            avg_risk = avg_risk / len(rows)
            pf_df = pd.DataFrame(rows)

            colA, colB, colC, colD = st.columns(4)
            with colA:
                st.metric("Portfolio Value", f"₹{round(total_val/1e5,2)} L")
            with colB:
                st.metric("Holdings", len(rows))
            with colC:
                st.metric("At Risk (>=60)", risky_count)
            with colD:
                st.metric("Avg Risk", round(avg_risk, 1))

            # Heatmap
            st.markdown("### 📊 Risk Heatmap")
            fig = px.imshow(
                [pf_df["risk_score"]],
                color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
                labels=dict(color="Risk"),
                aspect="auto",
            )
            fig.update_xaxes(
                ticktext=pf_df["symbol"],
                tickvals=list(range(len(pf_df["symbol"]))),
                tickangle=45
            )
            fig.update_yaxes(showticklabels=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Pie chart by Value
            st.markdown("### 🥧 Allocation by Value")
            fig2 = px.pie(
                pf_df,
                names="symbol",
                values="value",
                color="symbol",  # categorical colors
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            fig2.update_traces(textinfo="percent+label", pull=[0.05]*len(pf_df))
            st.plotly_chart(fig2, use_container_width=True)

            # Pie chart by Quantity
            st.markdown("### 📊 Allocation by Quantity")
            fig3 = px.pie(
                pf_df,
                names="symbol",
                values="pnl",  # show relative profits/losses
                color="symbol",
                color_discrete_sequence=px.colors.qualitative.Pastel1,
                hole=0.3
            )
            fig3.update_traces(textinfo="percent+label", pull=[0.05]*len(pf_df))
            st.plotly_chart(fig3, use_container_width=True)

            # P&L table
            st.markdown("### 📑 P&L Snapshot")
            st.dataframe(
                pf_df[["symbol", "value", "pnl", "risk_score"]],
                use_container_width=True,
                height=250
            )
    else:
        st.info("Upload or configure your portfolio.json to view portfolio insights.")

    st.divider()

    # --- Announcements ---
    st.markdown("## 📢 Latest Announcements")
    if anns:
        df_anns = pd.DataFrame(anns).head(8)
        for _, r in df_anns.iterrows():
            risk_tag = _risk_badge(r.get("risk_score", 50))
            st.markdown(f"**{r.get('title','Untitled')}** ({r.get('date','')}) — {risk_tag}")
            if r.get("link"):
                st.caption(f"[🔗 Official Link]({r['link']})")
    else:
        st.info("No announcements available.")

    st.divider()

    # --- News ---
    st.markdown("## 📰 News Feed")
    if news:
        df_news = pd.DataFrame(news).head(10)
        for _, r in df_news.iterrows():
            risk_tag = _risk_badge(r.get("risk_score", 40))
            st.markdown(f"- {r.get('title','No title')} ({r.get('date','')}) — {risk_tag}")
    else:
        st.info("No news available.")

    st.divider()

    # --- Sector Snapshot ---
    st.markdown("## 🧭 Sector Overview")
    if sectors:
        sec_rows = []
        for sec, syms in sectors.items():
            rs = np.random.randint(20, 90)  # placeholder sector risk
            sec_rows.append({"sector": sec, "avg_risk": rs})
        sec_df = pd.DataFrame(sec_rows)
        fig4 = px.bar(
            sec_df,
            x="sector",
            y="avg_risk",
            color="avg_risk",
            color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
            title="Sector Risk Levels"
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(sec_df, use_container_width=True, height=200)
    else:
        st.info("No sector data.")

    st.divider()

    # --- Top Movers ---
    st.markdown("## 🚀 Top Movers (Demo)")
    movers = [
        {"symbol": "RELIANCE.BSE", "chg": +3.2},
        {"symbol": "TCS.BSE", "chg": -2.1},
        {"symbol": "HDFC.BSE", "chg": +4.0},
    ]
    mv_df = pd.DataFrame(movers)
    fig5 = px.bar(
        mv_df,
        x="symbol",
        y="chg",
        color="chg",
        color_continuous_scale=["#e74c3c", "#2ecc71"],
        title="Top Gainers / Losers"
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.divider()

    # Footer
    st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
