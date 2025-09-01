
# Announcement Credibility Pro — SEBI Demo

**Hero:** Credibility scoring of corporate announcements with explainability.  
**Plus:** Similar Past Cases, Evidence Vault, Pump/Group mini-surveillance, and **BSE Ingestion (demo-safe)**.

## Run (Windows PowerShell)
```
cd market_credibility_pro
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Data sources
- **Demo:** `samples/announcements_demo.csv` (with labels for model training)
- **Ingested:** From Tab 1 (BSE ingest) → `samples/ingested.csv`
- **Upload:** Your CSV

### CSV columns
`date, company, sector, ann_type, headline, body, claimed_deal_cr, counterparty, timeline_months, has_attachment`

## Ingestion (BSE)
- Tries respectful online fetch (requests + bs4). If unavailable or blocked, **falls back to `samples/bse_sample.html`** to keep the demo reliable.
- Preview → select rows → **Ingest** to `samples/ingested.csv`.
- Then score them from the Upload/Score tab by choosing **Ingested** as source.

## Next-priority optimizations (for judges)
- LightGBM + probability calibration (tabular)
- MiniLM embeddings (text) + SHAP bars in UI
- Official exchange API adapters / formal access
- Counterparty registry APIs (MCA, sector boards)
- Alert routing + case management (email/webhooks)
