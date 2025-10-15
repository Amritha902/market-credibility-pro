import streamlit as st
from ui.components.helpers import advisor_entity_check

def render():
    st.subheader("Advisor / Entity Check")
    q = st.text_input("Enter SEBI ID / LEI / ISIN / CIN / Legal Name")
    if st.button("Check") and q:
        res = advisor_entity_check(q.strip())
        st.json(res)
        st.caption("SEBI IA example: IA123456 • LEI: 20 chars • ISIN: 12 chars • CIN: Indian company identifier")
