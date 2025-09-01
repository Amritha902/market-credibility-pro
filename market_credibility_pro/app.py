
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

from core.rules import rule_score
from core.tabular_model import build_features, fit_model, predict_proba
from core.text_model import TextModel
from core.fuse import fuse
from core.similar import similar_past_cases
from core.evidence import evidence_bundle, append_log
from ingestors.bse import fetch_bse_latest

st.set_page_config(page_title="Announcement Credibility Pro — SEBI Demo", layout="wide")
st.markdown("# 🧭 Announcement Credibility Pro — SEBI Demo")
st.caption("Explainable scoring of corporate announcements + Similar Past Cases + Evidence Vault + Pump/Group mini-surveillance + **BSE Ingestion (demo-safe)**.")

baseline = pd.read_csv("data/issuer_baseline.csv")
registry = set(pd.read_csv("data/counterparty_registry.csv")["name"].tolist())

def load_demo_ann():
    return pd.read_csv("samples/announcements_demo.csv")

def load_ingested():
    p = Path("samples/ingested.csv")
    return pd.read_csv(p) if p.exists() else None

def mk_announcement_id(i):
    return f"DEMO-{i:04d}"

tabs = st.tabs(["Fetch (BSE Ingest)", "Upload/Score", "Detail & Evidence", "Regulator Dashboard", "Pump/Group Mini"])

if "ann_df" not in st.session_state:
    st.session_state["ann_df"] = None

# -------- Tab 1: BSE Ingest --------
with tabs[0]:
    st.subheader("Fetch latest BSE announcements (safe fallback to local sample)")
    col1, col2 = st.columns([1,1])
    with col1:
        limit = st.slider("How many to fetch", 5, 40, 20, step=5)
    with col2:
        online = st.checkbox("Try online fetch (if internet available)", value=True)
    if st.button("Fetch & Preview"):
        items = fetch_bse_latest(limit=limit, use_online=online)
        ing = pd.DataFrame(items)
        if ing.empty:
            st.warning("No rows parsed. Try lowering limit or disable online fetch to use sample fallback.")
        else:
            st.markdown("### Preview")
            st.dataframe(ing, use_container_width=True)
            st.session_state["ing_preview"] = ing
    if "ing_preview" in st.session_state:
        dfp = st.session_state["ing_preview"].copy()
        dfp["accept"] = True
        edited = st.data_editor(dfp, use_container_width=True, num_rows="dynamic")
        if st.button("Ingest accepted rows"):
            acc = edited[edited["accept"]==True].drop(columns=["accept"])
            if not acc.empty:
                acc.to_csv("samples/ingested.csv", index=False)
                st.success(f"Ingested {len(acc)} rows → samples/ingested.csv")
            else:
                st.info("No rows selected to ingest.")

# -------- Tab 2: Upload/Score --------
with tabs[1]:
    st.subheader("Choose data source and score announcements")
    source = st.radio("Data source", ["Demo (included)", "Ingested (from Tab 1)", "Upload CSV"], horizontal=True)
    DATA_FEED_BADGE = st.empty()

    up = None
    if source == "Demo (included)":
        DATA_FEED_BADGE.info("Using **Demo Data** (`samples/announcements_demo.csv`)")
        ann = load_demo_ann()
    elif source == "Ingested (from Tab 1)":
        ing = load_ingested()
        if ing is None or ing.empty:
            DATA_FEED_BADGE.warning("No ingested data found yet. Use Tab 1 to fetch & ingest.")
            ann = load_demo_ann()
        else:
            DATA_FEED_BADGE.success("Using **Ingested Data** (`samples/ingested.csv`)")
            ann = ing
    else:
        up = st.file_uploader("Upload announcements CSV", type=["csv"])
        if up is not None:
            DATA_FEED_BADGE.success("Using **Uploaded Data**")
            ann = pd.read_csv(up)
        else:
            DATA_FEED_BADGE.info("Awaiting upload… Using **Demo Data** until a file is provided.")
            ann = load_demo_ann()

    ann = ann.copy()
    if "announcement_id" not in ann.columns:
        ann["announcement_id"] = [mk_announcement_id(i) for i in range(1, len(ann)+1)]

    # Train on demo labels (keeps training stable)
    demo = load_demo_ann().copy()
    feat_train = build_features(demo, baseline, registry)
    from core.tabular_model import fit_model
    tab_model = fit_model(feat_train.assign(label_credible=demo["label_credible"]))
    txt_model = TextModel().fit(demo)

    # Build features for picked set and score
    feat = build_features(ann, baseline, registry)
    proba_tab = predict_proba(tab_model, feat)
    proba_txt = txt_model.proba(ann)

    scores = []; checks_list = []; reasons_list = []
    for idx, row in ann.iterrows():
        base_row = baseline[baseline["company"]==row["company"]]
        if base_row.empty:
            base_row = baseline.sample(1, random_state=42)
        score, lvl, reasons, checks = rule_score(row, base_row.iloc[0], registry)
        scores.append(score); reasons_list.append(reasons); checks_list.append(checks)

    final = fuse(scores, proba_tab, proba_txt, w=(0.5,0.3,0.2))
    levels = [("Low" if s>70 else ("Medium" if s>=35 else "High")) for s in final]

    out = ann.copy()
    out["rule_score"] = np.round(scores,2)
    out["tabular_proba"] = np.round(proba_tab,3)
    out["text_proba"] = np.round(proba_txt,3)
    out["final_score"] = np.round(final,2)
    out["risk_level"] = levels
    out["reasons"] = reasons_list
    out["checks"] = checks_list

    st.session_state["ann_df"] = out

    st.markdown("### Results")
    # Heat-gauge column
    try:
        st.dataframe(
            out[["announcement_id","date","company","sector","ann_type","headline","final_score","risk_level"]]
            .sort_values("final_score"),
            use_container_width=True,
            column_config={
                "final_score": st.column_config.ProgressColumn(
                    "Credibility",
                    min_value=0, max_value=100, format="%.0f"
                )
            }
        )
    except Exception:
        st.dataframe(out.sort_values("final_score"), use_container_width=True)

    colA, colB, colC = st.columns(3)
    with colA: st.markdown(":red_circle: **High Risk** `<35`")
    with colB: st.markdown(":large_yellow_circle: **Medium** `35–70`")
    with colC: st.markdown(":green_circle: **Low** `>70`")

# -------- Tab 3: Detail & Evidence --------
with tabs[2]:
    st.subheader("Drilldown: reasons, similar past cases, and evidence")
    df = st.session_state.get("ann_df")
    if df is None or df.empty:
        st.info("Score announcements first in the 'Upload/Score' tab.")
    else:
        sel = st.selectbox("Select announcement ID", df["announcement_id"])
        row = df[df["announcement_id"]==sel].iloc[0]
        colL, colR = st.columns([2,1])

        with colL:
            st.markdown(f"### {row['company']} — {row['headline']}")
            st.caption(f"{row['date']} · {row['sector']} · {row['ann_type']}")
            st.write(row["body"])

            checks = row["checks"]
            def ck(b): return "✅" if b else "❌"
            st.markdown(f"**Corroboration signals:**  Counterparty {ck(checks['counterparty_named'])} · Timeline {ck(checks['timeline_specified'])} · Financials {ck(checks['financial_disclosed'])} · Attachment {ck(checks['attachment_present'])} · Registry {ck(checks['registry_match'])}")

            st.markdown("**Reasons (explainability):**")
            for r in row["reasons"]:
                st.write(f"- {r}")
            st.markdown(f"**Scores:** Rule {row['rule_score']} · Tabular ML {row['tabular_proba']:.2f} · Text ML {row['text_proba']:.2f} → **Final {row['final_score']} ({row['risk_level']})**")

            st.markdown("#### Counterfactual: adjust claimed value (what-if)")
            new_claim = st.slider("Claimed deal value (₹ crore)", min_value=0, max_value=int(max(50, row.get("claimed_deal_cr",0)*2+100)), value=int(row.get("claimed_deal_cr",0)))
            tmp = row.copy(); tmp["claimed_deal_cr"] = new_claim
            base_row = baseline[baseline["company"]==row["company"]]
            if base_row.empty:
                base_row = baseline.sample(1, random_state=42)
            score_new, lvl_new, reasons_new, checks_new = rule_score(tmp, base_row.iloc[0], registry)
            fused_new = 0.5*score_new + 0.3*row["tabular_proba"]*100 + 0.2*row["text_proba"]*100
            st.write(f"New fused score: **{np.round(fused_new,2)}** (old: {row['final_score']})")
            if fused_new > row["final_score"]:
                st.success("Lower claim improves credibility.")
            elif fused_new < row["final_score"]:
                st.warning("Higher claim reduces credibility.")

            # Mock next-step hook
            if st.button("Cross-verify with MCA (mock)"):
                st.info("Would connect to MCA/Ministry registries for counterparty validation in a pilot.")

        with colR:
            st.markdown("### Similar Past Cases")
            history = pd.read_csv("samples/cases_history.csv")
            sim, summary = similar_past_cases(row, history)
            st.write(f"{summary['similar_count']} similar cases · Verified: {summary['verified']} · Pending: {summary['pending']} · Retracted: {summary['retracted']}")
            st.dataframe(sim, use_container_width=True)

            st.markdown("### Text signals")
            tm = TextModel().fit(load_demo_ann())
            txt = (str(row["headline"])+" "+str(row["body"]))
            terms = tm.top_terms_for_row(txt, topk=8)
            if terms:
                for t, c in terms:
                    st.write(f"- {t} ({c:+.3f})")
            else:
                st.write("No dominant terms.")

            st.markdown("### Evidence bundle")
            ann_obj = {k: row[k] for k in ["announcement_id","date","company","sector","ann_type","headline","body","counterparty"] if k in row}
            features_obj = {k: (row[k] if k in row else None) for k in ["rule_score","tabular_proba","text_proba"]}
            score_obj = {"score": float(row["final_score"]), "level": row["risk_level"], "reasons": row["reasons"], "checks": row["checks"]}
            bundle = evidence_bundle(ann_obj, features_obj, score_obj, model_version={"tabular":"p0.1","text":"p0.1","rules":"p0.1"})
            js = __import__("json").dumps(bundle, indent=2)
            st.code(js)
            st.download_button("Download evidence.json", data=js, file_name=f"{row['announcement_id']}_evidence.json", mime="application/json")
            append_log(bundle)

# -------- Tab 4: Regulator Dashboard --------
with tabs[3]:
    st.subheader("Regulator Dashboard — triage by credibility")
    df = st.session_state.get("ann_df")
    if df is None or df.empty:
        st.info("Score announcements first.")
    else:
        low = df.nsmallest(5, "final_score")[["announcement_id","company","sector","ann_type","headline","final_score","risk_level"]]
        st.markdown("### 🔴 High-priority (lowest scores)")
        st.dataframe(low, use_container_width=True)
        heat = df.groupby(["sector","ann_type"])["final_score"].mean().reset_index()
        chart = alt.Chart(heat).mark_rect().encode(
            x=alt.X("sector:N"),
            y=alt.Y("ann_type:N"),
            color=alt.Color("final_score:Q", title="Avg Score"),
            tooltip=["sector","ann_type","final_score"]
        )
        st.altair_chart(chart, use_container_width=True)

# -------- Tab 5: Pump/Group Mini --------
with tabs[4]:
    st.subheader("Pump-and-Dump Mini — upload chat CSV (ts, user, text)")
    upc = st.file_uploader("Upload chat CSV", type=["csv"], key="chat_up")
    if upc is None:
        st.info("Using demo chat")
        chat = pd.read_csv("samples/chat_demo.csv")
    else:
        chat = pd.read_csv(upc)
    from core.surveillance import score_group
    res = score_group(chat)
    st.dataframe(res, use_container_width=True)
    bar = alt.Chart(res).mark_bar().encode(x="symbols:N", y="pump_risk:Q", tooltip=["symbols","mentions","pump_risk"])
    st.altair_chart(bar, use_container_width=True)
