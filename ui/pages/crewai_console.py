import streamlit as st
from crewai_layer.crew_orchestrator import run_crewai_check

def render():
    st.title("🤖 CrewAI Console")
    st.caption("Run collaborative AI agents to verify announcements and documents.")

    claim = st.text_area("Enter claim/announcement")
    url = st.text_input("Optional URL")
    company = st.text_input("Optional company symbol")

    if st.button("Run CrewAI Agents"):
        if not claim.strip():
            st.warning("Please enter a claim.")
            return
        with st.spinner("Running CrewAI agents..."):
            res = run_crewai_check(claim, url, company)
        st.success("CrewAI run complete")
        st.json(res)
