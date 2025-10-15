import streamlit as st
from ui.components.helpers import get_supabase

def render():
    st.subheader("Detail & Evidence")
    sb = get_supabase(write=False)
    if not sb:
        st.error("Supabase not configured. Add SUPABASE_URL and keys.")
        return
    try:
        res = sb.table("evidence_cases").select("*").order("created_at", desc=True).limit(25).execute()
        items = res.data or []
        if not items:
            st.info("No evidence records yet.")
        for it in items:
            st.json(it.get("payload", {}))
    except Exception as e:
        st.error(f"Error reading evidence: {e}")
