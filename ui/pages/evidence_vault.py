import streamlit as st, json
from ui.components.helpers import get_supabase

def render():
    st.subheader("Evidence Vault")
    sb = get_supabase(write=True)
    if not sb:
        st.error("Supabase not configured (URL + SERVICE ROLE KEY)")
        return
    tab1, tab2 = st.tabs(["List", "Add manual record"])
    with tab1:
        try:
            res = sb.table("evidence_cases").select("*").order("created_at", desc=True).limit(50).execute()
            for it in (res.data or []):
                st.json(it.get("payload", {}))
        except Exception as e:
            st.error(f"Read error: {e}")
    with tab2:
        payload = st.text_area("JSON payload", value='{"note":"manual evidence"}', height=180)
        if st.button("Insert"):
            try:
                js = json.loads(payload)
                sb.table("evidence_cases").insert({"payload": js}).execute()
                st.success("Inserted")
            except Exception as e:
                st.error(f"Insert error: {e}")
