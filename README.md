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
looks:
<img width="1919" height="868" alt="image" src="https://github.com/user-attachments/assets/8c38cc8d-472f-499b-9d47-6102555b4957" />
<img width="1918" height="871" alt="image" src="https://github.com/user-attachments/assets/0e59c4e7-4189-4c57-abaf-6066b61d1d63" />
<img width="1440" height="809" alt="image" src="https://github.com/user-attachments/assets/6aa653f5-3162-4559-950b-a3566f747779" />
<img width="1919" height="853" alt="image" src="https://github.com/user-attachments/assets/e3cd382b-8a96-4aab-9550-c4e36f2245a1" />
<img width="1919" height="839" alt="image" src="https://github.com/user-attachments/assets/085fb1bf-a495-42c4-b7f6-7761fb4a41b8" />
<img width="1914" height="846" alt="image" src="https://github.com/user-attachments/assets/d40d9428-139a-4a37-b874-acadf2ae114e" />
<img width="1918" height="859" alt="image" src="https://github.com/user-attachments/assets/e54abc7a-78da-47c5-bd84-5aaf4b91a22b" />
<img width="1917" height="840" alt="image" src="https://github.com/user-attachments/assets/5ff640ee-3b1e-4a6b-9fa7-3533a09925e4" />
different datasets:
<img width="1462" height="805" alt="image" src="https://github.com/user-attachments/assets/03892809-c0a4-4d13-b240-6c7d7619e6c9" />
<img width="1462" height="805" alt="image" src="https://github.com/user-attachments/assets/4fdd1529-3ad3-410c-bbe0-f7c7621254bb" />







## v6 Changes
- Robust CSV validation: auto-coerce NaN/None strings (no Pydantic crashes).
- Pump/Group CSV hardened (quoted sample + tolerant parser).
- Global CSV loader fallback (engine='python', on_bad_lines='skip').
- UI label updated to v6.
