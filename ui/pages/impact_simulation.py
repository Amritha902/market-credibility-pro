import streamlit as st
from ui.components.helpers import gemini_summarize

def render():
    st.subheader("Impact Simulation")
    st.write("Run a simple 'what-if' scenario and get AI commentary.")
    scenario = st.text_area("Scenario (e.g., 'Company X announces US FDA approval of drug Y')")
    if st.button("Simulate & Explain"):
        st.metric("Estimated Short-term Impact", "+2.4%")
        st.metric("Estimated 20D Volume Uplift", "+14%")
        st.write("AI Commentary:")
        st.write(gemini_summarize(f"Explain likely market impact of: {scenario}. Keep it concise."))
