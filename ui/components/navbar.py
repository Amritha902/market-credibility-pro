import streamlit as st
from pathlib import Path

PAGES = [
    ("Market & Scores", "market"),
    ("Impact Simulation", "impact"),
    ("Sector Risk Dashboard", "sector"),
    ("Detail & Evidence", "evidence"),
    ("Fetch & Ingest (BSE)", "ingest"),
    ("Document Verifier", "docs"),
    ("Advisor/Entity Check", "advisor"),
    ("Pump/Group Mini", "pump"),
    ("Evidence Vault", "vault"),
    ("Chat", "chat"),
]

def apply_theme():
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    css = '''<style>
      :root { --bg:#ffffff; --fg:#0f172a; --muted:#475569; --brand:#1b3d6d; --border:#e5e7eb; }
      .dark { --bg:#0b1220; --fg:#e5e7eb; --muted:#9aa4b2; --brand:#7aa2ff; --border:#1f2937; }
      .ic-top { position:sticky; top:0; z-index:999; background:var(--bg); border-bottom:1px solid var(--border); padding:10px;}
      .ic-title { font-weight:700; color:var(--brand); }
    </style>'''
    st.markdown(css, unsafe_allow_html=True)

def current_page() -> str:
    if "page" not in st.session_state:
        st.session_state.page = "market"
    return st.session_state.page

def render_topbar(title: str = "InfoCrux"):
    theme_class = "dark" if st.session_state.get("theme") == "dark" else ""
    st.markdown(f'<div class="ic-top {theme_class}">', unsafe_allow_html=True)
    left, mid, right = st.columns([2,6,2])
    with left:
        st.markdown(f'<div class="ic-title">{title}</div>', unsafe_allow_html=True)
    with mid:
        cols = st.columns(len(PAGES))
        for i, (label, key) in enumerate(PAGES):
            with cols[i]:
                if st.button(label, key=f"nav_{key}"):
                    st.session_state.page = key
    with right:
        logo_path = Path.cwd() / "logo.png"
        if logo_path.exists():
            st.image(str(logo_path), width=120)
        dark_on = st.toggle("Dark", value=(st.session_state.get("theme") == "dark"))
        st.session_state.theme = "dark" if dark_on else "light"
    st.markdown("</div>", unsafe_allow_html=True)
