# InfoCrux Final

AI-powered credibility engine for SEBI Hackathon.

## 🚀 Features
- Announcement verification (BSE/NSE/SEBI scrapers)
- Intelligent JSON lookup + registry cross-check
- Document verifier (PDF, DOCX, PPTX, Images, OCR, Audio/Video → Text)
- Market & Scores (TA indicators, charts, donut, histogram)
- Sector Dashboard (heatmap risk overview)
- Advisor Check (ISIN, LEI, SEBI ID, CIN validators)
- Pump/Group anomaly detection
- Evidence Vault (Supabase-backed)
- Chat interface with history
- Impact Simulation (stock indicators & risk)

## 📂 Project Structure
See folders: `ui/`, `core/`, `config/`, `data/`, `samples/`, `assets/`.

## ⚙️ Setup
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# fill in your API keys in .env
```

## ▶️ Run
```bash
streamlit run ui/app.py
```
or use:
- `start.bat` (Windows)
- `run_demo.sh` (Linux/Mac)

## 📊 Demo Data
If API limits are hit, pages include a **Use Demo Data** button.
Demo files are in `samples/` and `data/`.
