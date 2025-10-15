@echo off
echo Starting InfoCrux...
call .venv\Scripts\activate
streamlit run ui\app.py
pause
