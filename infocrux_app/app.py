# --- path bootstrap ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import altair as alt
from infocrux_app.core.logging_setup import setup_logger
from infocrux_app.core.utils import here, load_csv, badge_for_level

# ---- UI Theming (subtle iOS-like) ----
def ui_style():
    import streamlit as st
    st.markdown(
        '''<style>
        .block-container{padding-top:1.2rem;padding-bottom:2rem;}
        body{background:#f6f7f8;}
        .stButton>button{border-radius:14px;box-shadow:0 2px 8px rgba(0,0,0,0.06);} 
        .stTextInput>div>div>input, .stNumberInput input, .stSelectbox>div>div{border-radius:14px;}
        .stAlert{border-radius:12px;}
        .ios-card{background:white;border-radius:16px;padding:16px;box-shadow:0 4px 16px rgba(0,0,0,0.06);}
        .centered{display:flex;justify-content:center;align-items:center;}
        </style>''', unsafe_allow_html=True)


# ---- Guided Flow Helpers ----
def set_section(name: str):
    st.session_state["section"] = name
    st.rerun()

def show_pending_dialog():
    pd = st.session_state.get("pending_dialog")
    if not pd:
        return
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.markdown(f"### {pd.get('title','Done')}")
        st.write(pd.get("msg",""))
        c1, c2 = st.columns(2)
        next_sec = pd.get("next")
        with c1:
            if st.button(f"OK{'' if not next_sec else f' — Go to {next_sec}'}"):
                if next_sec:
                    st.session_state.pop("pending_dialog", None)
                    set_section(next_sec)
                else:
                    st.session_state.pop("pending_dialog", None)
                    st.experimental_rerun()
        with c2:
            if st.button("Stay here"):
                st.session_state.pop("pending_dialog", None)
                st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def notify_ok(msg: str):
    import streamlit as st
    try:
        st.toast(msg)
    except Exception:
        st.success(msg)

from infocrux_app.core.schema import validate_announcements_df
from infocrux_app.core.rules import rule_score, rule_reasons
from infocrux_app.core.tabular_model import train_tabular, predict_tabular
from infocrux_app.core.text_model import train_text, predict_text, text_signals
from infocrux_app.core.fusion import fuse_scores, level_from_score
from infocrux_app.core.evidence import evidence_bundle, append_log
from infocrux_app.core.config import EVIDENCE_LOG
from infocrux_app.ingestors.bse import fetch_bse_latest

st.set_page_config(page_title="InfoCrux — Announcement Credibility Pro (v6.4)", layout="wide")
logger = setup_logger()

logo = here("assets/infocrux_logo.png")
if logo.exists():
    st.sidebar.image(logo.as_posix(), width=140)
st.sidebar.markdown("### InfoCrux")
st.sidebar.caption("Announcement Credibility Pro — SEBI Hackathon")

section = st.sidebar.radio("Navigate", [
    "📊 Market & Scores",
    "🔮 Impact Simulation",
    "🌡️ Sector Risk Dashboard",
    "🔍 Detail & Evidence",
    "📥 Fetch & Ingest (BSE)",
    "🛡️ Document Verifier",
    "🔎 Advisor/Entity Check",
    "💬 Pump/Group Mini",
    "📂 Evidence Vault",
])

show_pending_dialog()
st.title("📊 InfoCrux — Announcement Credibility Pro (v6.4)")

@st.cache_data
def demo_announcements():
    return load_csv("samples/announcements_demo.csv")

@st.cache_data
def cases_history():
    return load_csv("samples/cases_history.csv")

def ensure_id(df: pd.DataFrame):
    df = df.copy()
    if "id" not in df.columns:
        df["id"] = [f"ANN-{i:04d}" for i in range(1, len(df)+1)]
    return df

@st.cache_resource
def build_models(training_df: pd.DataFrame):
    X = training_df.copy()
    return train_tabular(X), train_text(X)

def score_dataframe(df: pd.DataFrame, models=None):
    df = ensure_id(df)
    r = rule_score(df)
    if models is None:
        tab_model, txt_model = build_models(df)
    else:
        tab_model, txt_model = models
    tprob = predict_tabular(tab_model, df)
    xprob = predict_text(txt_model, df)
    fused = fuse_scores(r, tprob, xprob)
    out = df.copy()
    out["rule_score"] = r.round(2)
    out["tabular_prob"] = tprob.round(3)
    out["text_prob"] = xprob.round(3)
    out["final_score"] = fused.round(2)
    out["risk_level"] = out["final_score"].apply(level_from_score)
    return out.sort_values("final_score", ascending=False)

if "data" not in st.session_state:
    st.session_state["data"] = demo_announcements()
if "models" not in st.session_state:
    cleaned, _ = validate_announcements_df(st.session_state["data"])
    st.session_state["models"] = build_models(cleaned)
if "scored" not in st.session_state:
    cleaned, _ = validate_announcements_df(st.session_state["data"])
    st.session_state["scored"] = score_dataframe(cleaned, st.session_state["models"])

def claim_bucket(v: float) -> str:
    if v < 50: return "0-50"
    if v < 100: return "50-100"
    if v < 200: return "100-200"
    if v < 500: return "200-500"
    if v < 1000: return "500-1000"
    if v < 2000: return "1000-2000"
    return "2000-6000"

def similar_cases_view(row: dict):
    hist = cases_history()
    bucket = claim_bucket(float(row.get("claimed_deal_cr",0)))
    subset = hist[(hist["sector"]==row.get("sector","")) & (hist["ann_type"]==row.get("ann_type","")) & (hist["claim_bucket"]==bucket)]
    if subset.empty:
        return pd.DataFrame(), {"Verified":0,"Pending":0,"Retracted":0}
    counts = subset["outcome"].value_counts().to_dict()
    for k in ["Verified","Pending","Retracted"]:
        counts.setdefault(k,0)
    return subset, counts

if section == "📊 Market & Scores":
    st.caption("Upload CSV to score or use demo data. Required columns: date, company, sector, ann_type, headline, body, claimed_deal_cr, counterparty, timeline_months, has_attachment.")
    up = st.file_uploader("Upload announcements CSV", type=["csv"])
    if up is not None:
        raw = pd.read_csv(up)
        cleaned, errors = validate_announcements_df(raw)
        if errors:
            st.error("CSV has issues:\n- " + "\n- ".join(errors))
        else:
            st.session_state.data = cleaned
            st.session_state.models = build_models(cleaned)
            st.session_state.scored = score_dataframe(cleaned, st.session_state.models)
            st.success("Uploaded & scored successfully.")
            logger.info("Uploaded CSV rows=%d", len(cleaned))
    if st.button("Load Demo Data"):
        df = demo_announcements()
        cleaned, _ = validate_announcements_df(df)
        st.session_state.data = cleaned
        st.session_state.models = build_models(cleaned)
        st.session_state.scored = score_dataframe(cleaned, st.session_state.models)
        st.success("Demo data loaded.")

    scored = st.session_state.scored
    c1,c2,c3 = st.columns(3)
    c1.metric("Announcements Scored", len(scored))
    c2.metric("High Risk", f"{(scored['risk_level']=='High').mean()*100:.1f}%")
    c3.metric("Avg Score", f"{scored['final_score'].mean():.1f}")

    dist = scored.groupby("risk_level", as_index=False).size()
    donut = alt.Chart(dist).mark_arc(innerRadius=60).encode(
        theta="size:Q",
        color=alt.Color("risk_level:N", legend=None),
        tooltip=["risk_level","size"]
    ).properties(height=260)
    by_sector = scored.groupby("sector", as_index=False)["final_score"].mean().sort_values("final_score")
    bar = alt.Chart(by_sector).mark_bar().encode(
        x="final_score:Q",
        y=alt.Y("sector:N", sort="-x"),
        tooltip=["sector","final_score"]
    ).properties(height=260)

    st.markdown("### Dashboard")
    cc1, cc2 = st.columns(2)
    with cc1: st.altair_chart(donut, use_container_width=True)
    with cc2: st.altair_chart(bar, use_container_width=True)

    # Histogram of final scores
    hist = alt.Chart(scored).mark_bar().encode(
        x=alt.X('final_score:Q', bin=alt.Bin(maxbins=20), title='Final Score'),
        y='count()', tooltip=['count()']
    ).properties(height=200)
    st.altair_chart(hist, use_container_width=True)

    show = scored[["id","date","company","sector","ann_type","headline","final_score","risk_level"]].copy()
    show["risk"] = show["risk_level"].apply(lambda x: badge_for_level(x))
    st.write("**Results**")
    st.write(show.to_html(escape=False, index=False), unsafe_allow_html=True)

    with st.expander("🔎 View current dataset (raw input)"):
        st.dataframe(st.session_state.data, use_container_width=True)
        st.download_button("Download current dataset CSV", st.session_state.data.to_csv(index=False).encode("utf-8"),
                           file_name="announcements_current.csv", mime="text/csv")
    with st.expander("📥 Scored results (full columns)"):
        st.dataframe(scored, use_container_width=True)
        st.download_button("Download scored CSV", scored.to_csv(index=False).encode("utf-8"),
                           file_name="announcements_scored.csv", mime="text/csv")

elif section == "🔮 Impact Simulation":
    st.caption("Pick an announcement and explore *what-if* changes. Uses models trained on the full dataset for stability.")
    scored = st.session_state.scored
    sel_id = st.selectbox("Announcement", scored["id"])
    row = scored[scored["id"]==sel_id].iloc[0].to_dict()
    c1,c2,c3 = st.columns(3)
    mult = c1.slider("Deal Size Multiplier", 0.5, 3.0, 1.0, 0.1)
    no_cp = c2.checkbox("Remove Counterparty", False)
    no_att = c3.checkbox("Remove Attachment", False)
    sim = row.copy()
    sim["claimed_deal_cr"] = float(sim.get("claimed_deal_cr",0))*mult
    if no_cp: sim["counterparty"] = ""
    if no_att: sim["has_attachment"] = 0
    sim_df = pd.DataFrame([sim])
    sim_scored = score_dataframe(sim_df, st.session_state.models)
    old = float(row["final_score"]); new = float(sim_scored["final_score"].iloc[0])
    st.metric("New Score", f"{new:.2f}", delta=f"{new-old:+.2f}")
    st.write(sim_scored[["company","headline","final_score","risk_level"]])

elif section == "🌡️ Sector Risk Dashboard":
    scored = st.session_state.scored
    st.caption("Sector × Announcement Type — Average Credibility Score (lower is riskier).")
    agg = scored.groupby(["sector","ann_type"], as_index=False)["final_score"].mean()
    heat = alt.Chart(agg).mark_rect().encode(
        x=alt.X("sector:N", sort=agg["sector"].unique().tolist()),
        y=alt.Y("ann_type:N"),
        color=alt.Color("final_score:Q", title="Avg Score"),
        tooltip=["sector","ann_type","final_score"]
    )
    st.altair_chart(heat, use_container_width=True)

elif section == "🔍 Detail & Evidence":
    scored = st.session_state.scored
    sel_id = st.selectbox("Select announcement", scored["id"])
    row = scored[scored["id"]==sel_id].iloc[0].to_dict()

    from infocrux_app.core.config import BASE
    try:
        reg = set(pd.read_csv(BASE / "data" / "counterparty_registry.csv")["name"].str.lower().tolist())
    except Exception:
        reg = set()
    checks = {
        "counterparty_named": bool(row.get("counterparty","")),
        "timeline_specified": float(row.get("timeline_months",0))>=1,
        "financial_disclosed": float(row.get("claimed_deal_cr",0))>0,
        "attachment_present": float(row.get("has_attachment",0))>0,
        "registry_match": str(row.get("counterparty","")).lower() in reg,
    }
    reasons = rule_reasons(pd.Series(row))

    def claim_bucket(v: float) -> str:
        if v < 50: return "0-50"
        if v < 100: return "50-100"
        if v < 200: return "100-200"
        if v < 500: return "200-500"
        if v < 1000: return "500-1000"
        if v < 2000: return "1000-2000"
        return "2000-6000"
    hist = cases_history()
    bucket = claim_bucket(float(row.get("claimed_deal_cr",0)))
    sim_tbl = hist[(hist["sector"]==row.get("sector","")) & (hist["ann_type"]==row.get("ann_type","")) & (hist["claim_bucket"]==bucket)]
    counts = sim_tbl["outcome"].value_counts().to_dict() if not sim_tbl.empty else {}
    for k in ["Verified","Pending","Retracted"]: counts.setdefault(k,0)

    hits = text_signals(pd.Series(row))

    c1,c2 = st.columns([2,1])
    with c1:
        st.subheader(f"{row.get('company','')} — {row.get('headline','')}")
        st.caption(f"{row.get('date','')} · {row.get('sector','')} · {row.get('ann_type','')}")
        st.markdown("**Corroboration signals**: " + " · ".join([
            f"{k.replace('_',' ').title()} {'✅' if v else '❌'}" for k,v in checks.items()
        ]))
        st.markdown("**Reasons (explainability):**")
        for r in reasons: st.write(f"- {r}")
        st.markdown("**Text signals:** " + (", ".join(hits) if hits else "—"))

    with c2:
        st.metric("Final Score", f"{row.get('final_score',0):.2f}")
        st.markdown(badge_for_level(row.get('risk_level','')), unsafe_allow_html=True)
        st.markdown(f"**Similar Past Cases** — Verified: {counts['Verified']} · Pending: {counts['Pending']} · Retracted: {counts['Retracted']}")

    st.markdown("### Similar Past Cases (table)")
    if sim_tbl.empty:
        st.info("No closely similar past cases matched.")
    else:
        st.dataframe(sim_tbl, use_container_width=True)

    bundle = evidence_bundle(row, row.get("final_score",0), reasons, checks, model_version={"rules":"p0.4","tabular":"p0.4","text":"p0.4"})
    st.markdown("### Evidence bundle")
    st.json(bundle)
    if st.button("Append to Evidence Log"):
        append_log(bundle)
        st.success(f"Appended to {EVIDENCE_LOG.name}")


elif section == "📥 Fetch & Ingest (BSE)":
    st.caption("Attempts online fetch from BSE; if unavailable, uses bundled fallback and synthesizes to the requested count. Preview → Accept & Score.")
    st.info("Note: the ingestor now auto-cleans blank fields (e.g., missing counterparties) so you won't see validation crashes during demo.")
    limit = st.slider("How many announcements?", 5, 50, 20, 1)
    use_online = st.checkbox("Try online fetch", True)
    df = fetch_bse_latest(limit=limit, use_online=use_online)
    st.dataframe(df)
    if st.button("Accept & Score Preview"):
        cleaned, errors = validate_announcements_df(df)
        if errors:
            st.error("Fetched data has issues:\n- " + "\n- ".join(errors))
        else:
            st.session_state.data = cleaned
            st.session_state.models = build_models(cleaned)
            st.session_state.scored = score_dataframe(cleaned, st.session_state.models)
            st.success("Ingested and scored these announcements. See 'Market & Scores'.")

elif section == "💬 Pump/Group Mini":
    st.caption("Demo detection of pump-style group chatter from sample chat CSV.")
    import pandas as pd
    from infocrux_app.core.utils import here
    chat = pd.read_csv(here("samples/chat_demo.csv"), engine="python", on_bad_lines="skip")
    import numpy as np
    chat["risk"] = chat["text"].str.lower().apply(lambda s: int(any(t in s for t in ["rocket","upper circuit","sure shot","inside tip","dump","guaranteed"])))
    agg = chat.groupby("symbol", as_index=False)["risk"].sum().sort_values("risk", ascending=False)
    st.dataframe(agg)

elif section == "📂 Evidence Vault":

    import os, json
    from infocrux_app.core.utils import here
    st.subheader("📂 Evidence Vault")
    st.caption("Append-only JSONL log with SHA-256 hashes for auditability.")

    # Ensure storage exists
    storage_dir = here("storage")
    os.makedirs(storage_dir, exist_ok=True)
    log_file = here("storage/evidence_log.jsonl")
    if not os.path.exists(log_file):
        # create empty file
        with open(log_file, "w", encoding="utf-8") as _f:
            pass

    # Load rows
    rows = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # skip malformed lines
                continue

    st.write(f"Total evidence bundles: **{len(rows)}**")
    if rows:
        import pandas as pd
        # normalize a few top-level columns for display
        def flat(r):
            return {
                "announcement_id": r.get("announcement_id",""),
                "score": r.get("score",""),
                "level": r.get("level",""),
                "ingested_at": r.get("ingested_at",""),
                "raw_hash": r.get("raw_hash",""),
                "feature_hash": r.get("feature_hash",""),
                "company": (r.get("meta") or {}).get("company",""),
                "sector": (r.get("meta") or {}).get("sector",""),
                "ann_type": (r.get("meta") or {}).get("ann_type",""),
                "date": (r.get("meta") or {}).get("date",""),
            }
        dfv = pd.DataFrame([flat(r) for r in rows])
        st.dataframe(dfv, use_container_width=True)

        # Download full log
        with open(log_file, "rb") as f:
            st.download_button("Download evidence_log.jsonl", data=f.read(), file_name="evidence_log.jsonl", mime="application/json")

    else:
        st.info("No evidence entries yet. Open **🔍 Detail & Evidence** and click **Append to Evidence Log**.")
elif section == "📂 Evidence Vault":
    st.caption("Append-only log of all evidence bundles generated in this session.")
    log_path = EVIDENCE_LOG
    if log_path.exists():
        st.code(log_path.read_text(encoding="utf-8")[:30000])
    else:
        st.info("No entries yet. Generate from 'Detail & Evidence'.")

elif section == "🛡️ Document Verifier":
    st.caption("Upload a PDF purportedly from a regulator/intermediary. We extract text and run authenticity heuristics.")
    up = st.file_uploader("Upload PDF", type=["pdf"])
    if up is not None:
        from infocrux_app.core.doc_verify import verify_pdf
        b = up.read()
        res = verify_pdf(b)
        st.metric("Document Credibility", f"{res['score']}/100")
        st.markdown(f"**Level:** {res['level']}")
        st.write("**Checks:**", res["checks"])
        st.write("**Reasons:**")
        for r in (res["reasons"] or ["—"]):
            st.write(f"- {r}")
        st.code(res["excerpt"][:1200])
        st.caption(f"Doc hash: {res['doc_hash']}")

elif section == "🔎 Advisor/Entity Check":
    st.caption("Verify an advisor / RA / intermediary by name and optionally registration ID, using a local registry sample.")
    from infocrux_app.core.advisor_check import load_registry, check_entity
    from infocrux_app.core.config import BASE
    reg = load_registry(BASE / "data" / "registered_entities.csv")
    name = st.text_input("Entity / Advisor Name", value="Alpha Advisory LLP")
    rid = st.text_input("Registration ID (optional)", value="IA123456")
    if st.button("Check"):
        exact, fuzzy = check_entity(reg, name, rid)
        if exact:
            st.success(f"ID match found: {exact['name']} ({exact['type']}) — ID {exact['text_id']}")
        else:
            st.warning("No exact ID match found.")
        st.markdown("**Closest name matches:**")
        st.dataframe(pd.DataFrame(fuzzy)[["name","type","text_id","fuzzy_score"]])
