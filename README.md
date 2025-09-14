# InfoCrux — Announcement Credibility Pro (v6)
## New in v6
- 🛡️ Document Verifier (PDF heuristics + hash)
- 🔎 Advisor/Entity Check (registry + fuzzy match)
- Dashboard histogram

## Run (Windows)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run infocrux_app\app.py
```

## Docker
```bash
docker build -t infocrux:v6 .
docker run -p 8501:8501 infocrux:v6
```

## v6 Changes
- Robust CSV validation: auto-coerce NaN/None strings (no Pydantic crashes).
- Pump/Group CSV hardened (quoted sample + tolerant parser).
- Global CSV loader fallback (engine='python', on_bad_lines='skip').
- UI label updated to v6.
