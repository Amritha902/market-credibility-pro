# ui/pages/fetch_ingest.py
from __future__ import annotations

import streamlit as st

from ui.components.helpers import (
    read_pdf_text,
    verify_announcement,
    check_document_link,
    lookup_entity,
    suggest_official_sources,
    save_evidence,
)

def _render_refs(refs):
    if not refs:
        st.caption("—")
        return
    for u in refs[:12]:
        st.write(f"- {u}")

def render():
    st.subheader("Fetch & Ingest (BSE/NSE/SEBI)")

    c1, c2 = st.columns([2, 1])

    # ---- LEFT: text/link inputs ----
    with c1:
        title = st.text_input("Announcement title / summary", placeholder="e.g., ITC declares interim dividend")
        company = st.text_input("Company hint (optional)", placeholder="e.g., ITC, RELIANCE, TCS …")
        url = st.text_input("Announcement link (optional)", placeholder="Paste official URL if you have it")

        cbtn1, cbtn2 = st.columns(2)
        with cbtn1:
            run_live = st.button("Verify (Live)", use_container_width=True)
        with cbtn2:
            run_demo = st.button("Try Demo Claim", use_container_width=True)

        # Optional link hygiene (independent of verify)
        if url:
            st.markdown("**Link hygiene check**")
            lh = check_document_link(url)
            st.write(f"Verdict: **{lh.get('verdict','unknown')}**")
            rs = lh.get("reasons", [])
            if rs:
                st.caption("Reasons:")
                for r in rs:
                    st.write(f"- {r}")

    # ---- RIGHT: file upload (PDF only here for stability) ----
    with c2:
        st.caption("Or upload an announcement PDF to extract text")
        up = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        extracted_text = ""
        if up is not None:
            try:
                extracted_text = read_pdf_text(up.read())
                st.text_area("Extracted Text", value=extracted_text, height=220)
            except Exception as e:
                st.error(f"Could not read PDF: {e}")

    # ---- Determine the query text we will verify ----
    query_text = ""
    if run_demo:
        # A small, realistic demo string that triggers domain routing
        query_text = "Novapharm announces US FDA approval for oncology drug"
        company = "Novapharm"
        url = ""
    else:
        # prefer typed title; else short preview from PDF
        if title:
            query_text = title.strip()
        elif extracted_text:
            query_text = (extracted_text[:280] + "…") if len(extracted_text) > 280 else extracted_text

    # ---- Nothing to run yet ----
    if not (run_live or run_demo):
        st.info("Enter a title (or upload a PDF) and click **Verify (Live)**. Or click **Try Demo Claim** to see the flow.")
        return

    if not query_text:
        st.warning("There is nothing to verify. Please type a title or upload a PDF.")
        return

    # ---- Helpful context: suggest regulators from domain keywords BEFORE verify ----
    st.markdown("### Suggested official sources (based on keywords)")
    sugg = suggest_official_sources(" ".join([query_text or "", company or ""]))
    _render_refs([s["url"] for s in sugg])

    # ---- Local JSON/registry hit (fast) ----
    st.markdown("### Local registry match")
    lkp = lookup_entity(" ".join([query_text or "", company or ""]))
    if lkp.get("found"):
        st.success(
            f"Matched entity: **{lkp.get('entity')}** • Domain: {lkp.get('domain','—')} • "
            f"Registry: {lkp.get('source','—')} — {lkp.get('id','—')} • Valid till: {lkp.get('valid_till','—')}"
        )
        if lkp.get("official_sites"):
            st.caption("Known official sites:")
            _render_refs(lkp["official_sites"])
    else:
        st.caption("— no immediate local match")

    # ---- Official verification (scrapers + heuristics) ----
    st.markdown("### Verification against official sources")
    with st.spinner("Verifying…"):
        res = verify_announcement(query_text, company_hint=company or "", link=url or "")

    verdict = res.get("verdict", "unknown")
    reason = res.get("reason", "")
    st.write(f"**Verdict:** {verdict}")
    if reason:
        st.write(f"**Reason:** {reason}")

    # References come from helpers as 'references' inside official result
    official = (res.get("evidence") or {}).get("official") or {}
    refs = official.get("references") or []
    st.markdown("**References / where to check:**")
    _render_refs(refs)

    # Show we actually combined context
    with st.expander("What we checked (debug)"):
        st.json({
            "query_text": query_text,
            "company_hint": company,
            "url": url,
            "local_lookup_used": bool(lkp.get("found")),
            "suggested_sources": [s["url"] for s in sugg],
            "official_result": official,
        })

    # ---- Save evidence to Supabase (if configured) ----
    st.markdown("---")
    save_col1, save_col2 = st.columns([1, 3])
    with save_col1:
        do_save = st.button("Save evidence to Vault")
    with save_col2:
        st.caption("Stores this case in Supabase `evidence_cases` for the Detail & Evidence/Vault pages.")

    if do_save:
        evidence = res.get("evidence") or {}
        out = save_evidence(evidence)
        if out.get("ok"):
            st.success("Saved to Evidence Vault ✅")
        else:
            st.warning(f"Not saved: {out}")
