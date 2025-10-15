# --- bootstrap sys.path FIRST (so package-qualified imports work) ---
import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parents[1]  # .../<project-root>
if str(PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJ_ROOT))

# ---------------------- std / third-party ----------------------
import streamlit as st

# ---------------------- safe import helper ----------------------
def _safe_import(dotted: str, attr: str = "render"):
    """
    Import 'dotted' module and return its 'attr' (default: render) callable.
    If not found, returns a fallback function that shows a gentle message.
    """
    try:
        mod = __import__(dotted, fromlist=[attr])
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
        else:
            def _missing(dotted_name=dotted, attr_name=attr):
                st.warning(f"Page '{dotted_name}' is missing a callable `{attr_name}()`.")
            return _missing
    except Exception as err:
        # bind the exception object into the closure so it exists when called
        def _fallback(exc=err, dotted_name=dotted):
            st.error(f"Page '{dotted_name}' failed to load.")
            st.exception(exc)
        return _fallback

# ---------------------- page imports (package-qualified) ----------------------
page_main    = _safe_import("ui.pages.main", "render")              # <-- your Home page file
page_market  = _safe_import("ui.pages.market_scores", "render")
page_impact  = _safe_import("ui.pages.impact_simulation", "render")
page_sector  = _safe_import("ui.pages.sector_dashboard", "render")
page_evid    = _safe_import("ui.pages.detail_evidence", "render")
page_ingest  = _safe_import("ui.pages.fetch_ingest", "render")
page_docs    = _safe_import("ui.pages.document_verifier", "render")
page_advisor = _safe_import("ui.pages.advisor_check", "render")
page_pump    = _safe_import("ui.pages.pump_group", "render")
page_vault   = _safe_import("ui.pages.evidence_vault", "render")
page_chat    = _safe_import("ui.pages.chat", "render")

# ---------------------- CONFIG ----------------------
st.set_page_config(
    page_title="InfoCrux — Announcement Credibility Pro",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------- HEADER ----------------------
logo_path = PROJ_ROOT / "assets" / "logo.png"  # use assets/logo.png at repo root

top_l, top_r = st.columns([8, 1])
with top_l:
    st.markdown(
        """
        <h2 style="color:#2c3e50; margin-bottom:0;">
            InfoCrux — Announcement Credibility Pro
        </h2>
        <p style="color:#7f8c8d; font-size:16px; margin-top:4px;">
            AI-powered credibility engine for SEBI Hackathon
        </p>
        """,
        unsafe_allow_html=True
    )
with top_r:
    if logo_path.exists():
        st.image(str(logo_path), width=80)
    else:
        st.markdown("**InfoCrux**")

st.markdown("<hr style='margin:10px 0 16px 0;'>", unsafe_allow_html=True)

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    if logo_path.exists():
        st.image(str(logo_path))
    else:
        st.markdown("### InfoCrux")
    st.markdown("**Build status**: ✅ UI loaded")
    st.caption("- Use *Use Demo Data* when API limits hit.\n- Add your `.env` for live APIs.")
    st.markdown("---")
    st.caption("Project root: " + str(PROJ_ROOT))

# ---------------------- TOP NAVIGATION ----------------------
pages = {
    "Home": "main",  # <-- points to ui.pages.main
    "Market & Scores": "market",
    "Impact Simulation": "impact",
    "Sector Risk Dashboard": "sector",
    "Detail & Evidence": "evidence",
    "Fetch & Ingest (BSE)": "ingest",
    "Document Verifier": "docs",
    "Advisor Check": "advisor",
    "Pump/Group Mini": "pump",
    "Evidence Vault": "vault",
    "Chat": "chat",
}

selected = st.radio(
    "Navigation",
    options=list(pages.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

# ---------------------- ROUTER ----------------------
route = pages.get(selected, "main")

try:
    if route == "main":       page_main()
    elif route == "market":   page_market()
    elif route == "impact":   page_impact()
    elif route == "sector":   page_sector()
    elif route == "evidence": page_evid()
    elif route == "ingest":   page_ingest()
    elif route == "docs":     page_docs()
    elif route == "advisor":  page_advisor()
    elif route == "pump":     page_pump()
    elif route == "vault":    page_vault()
    elif route == "chat":     page_chat()
    else:                     page_main()
except Exception as e:
    st.error("⚠️ Something went wrong while loading the page.")
    st.exception(e)
