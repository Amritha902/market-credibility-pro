
import streamlit as st

def section(title: str, subtitle: str = ""):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)

def badge(text: str):
    st.markdown(f"<span style='background:#eef3ff;border:1px solid #d6e0ff;padding:2px 8px;border-radius:10px;font-size:12px;'>{text}</span>",
                unsafe_allow_html=True)

def chat_bubble(role: str, text: str):
    bg = "#f6f6f6" if role == "user" else "#eef9f0"
    st.markdown(
        f"<div style='background:{bg};padding:10px 12px;border-radius:10px;margin:6px 0;white-space:pre-wrap'>{text}</div>",
        unsafe_allow_html=True
    )
