# 📊 InfoCrux — Announcement Credibility Pro (SEBI Hackathon)
### link : https://infocrux.streamlit.app/
Theme: Fraud Prevention — Protecting retail investors from misleading / fabricated corporate announcements with explainable AI.
InfoCrux is an AI-powered tool designed to combat fraud in the financial markets. It assigns a Credibility Score (0–100) to corporate announcements, providing detailed explanations and corroboration checks to protect retail investors from pump-and-dump schemes and mispriced securities.

🎯 Why this matters
Misleading disclosures can trigger pump-and-dump schemes, misprice securities, and cause significant harm to retail investors. InfoCrux provides regulators, stock exchanges, and media with a fast, transparent way to triage risky announcements and understand precisely why they are flagged.

## ✨ Features (What’s actually built)
### 1. Market & Scores (Core)
Upload your own CSV or use the bundled demo to score announcements.

Utilizes a Fusion Scoring system: a blend of Rules, Tabular ML, and Text ML to generate a final score and risk level (High / Medium / Low).

Features a dashboard with a donut chart, sector bars, and a score histogram.

Allows you to download the scored CSV and view raw input side-by-side.

Screenshot of Dashboard:
<img width="1919" height="868" alt="image" src="https://github.com/user-attachments/assets/8c38cc8d-472f-499b-9d47-6102555b4957" />

### 2. Impact Simulation (What-if)
Choose an announcement and adjust key parameters like Deal size multiplier, or remove a counterparty or attachment.

See the instant score delta, a powerful feature for regulatory education and policy walkthroughs.

### 3. Sector Risk Dashboard
A heatmap visualizes the average credibility score by Sector × Announcement Type.

Easily identify "red zones" (e.g., Pharma Approvals, Vague Partnerships) with a single glance.

### 4. Detail & Evidence (Explainability)
Provides specific Reason codes (e.g., “Claim >> 6× historical median for this issuer”).

Displays Corroboration signals with clear ✅/❌ checks against counterparties, timelines, financials, and attachments.

Shows Similar Past Cases (Verified / Pending / Retracted) to provide historical context.

Generates an Evidence bundle JSON with hashes and model versions for audit purposes.

This bundle can be appended to an Evidence Vault for an immutable audit trail.

### 5. Other Tools & Features
Fetch & Ingest (BSE): Attempts to fetch and score the latest announcements from the BSE website.

Document Verifier (PDF): Upload a PDF document (e.g., a purported regulatory letter) to run heuristic checks on text and format, providing a credibility score.

Advisor/Entity Check: Verifies an advisor or intermediary against a local registry sample using both exact and fuzzy matching.

Pump/Group Mini (Signal): Analyzes chat logs to flag pump keywords and generate a quick symbol risk leaderboard.

Evidence Vault (Audit): An append-only log (evidence_log.jsonl) that stores all raw and processed data, scores, and model versions for full audit compliance.


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

## 🧠 Tech Stack
UI: Python, Streamlit

Data & ML: Pandas, NumPy, scikit-learn (LogReg pipelines, TF-IDF)

Charts: Altair

Web Scraping: BeautifulSoup, Requests

Security: SHA-256 hashing for audit trail integrity

Validation: Pydantic for robust CSV schema validation

## 🗂️ Data & Schemas
The application uses specific CSV schemas for its core functionality.

Required CSV Columns for Announcements:
| column | type | example |
|---|---|---|
| date | YYYY-MM-DD | 2025-08-18 |
| company | text | Nova Pharma |
| sector | enum | Pharma / Infra / IT / … |
| ann_type | enum | Approval / ProjectWin / Partnership / … |
| headline | text | Breakthrough drug wins fast-track nod |
| body | long text | Full announcement text |
| claimed_deal_cr | number (₹ crore) | 500 |
| counterparty | text | National Drug Authority |
| timeline_months | number | 3 |
| has_attachment | 0/1 | 1 |

## Demo Files (already in repo):

infocrux_app/samples/announcements_demo.csv

infocrux_app/samples/cases_history.csv

infocrux_app/samples/chat_demo.csv

infocrux_app/data/counterparty_registry.csv

infocrux_app/data/advisor_registry.csv

PDFs under infocrux_app/samples/

### 🚀 Quickstart

Follow these simple steps to get the application running locally.

```bash
# Clone the repository
git clone [https://github.com/Amritha902/market-credibility-pro.git](https://github.com/Amritha902/market-credibility-pro.git)
cd market-credibility-pro

# (Windows) create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# (macOS/Linux) create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run infocrux_app/app.py
## 🧭 How to Demo (5–7 min flow)
📥 Fetch & Ingest (BSE): Set the number of announcements to fetch, then click "Accept & Score."

📊 Market & Scores: Show the dashboard with the donut chart, sector bars, and histogram.

🔍 Detail & Evidence: Select an announcement from the table to show the reason codes, checks, and similar past cases.

🔮 Impact Simulation: Tweak the deal size or remove a counterparty to demonstrate the score's sensitivity.

🌡️ Sector Risk Dashboard: Highlight the heatmap for a high-level regulatory view.

📂 Evidence Vault: Show the growing evidence_log.jsonl and explain its use for audit.

🛡️ Document Verifier: Upload a sample PDF to show the heuristic checks.

🔎 Advisor/Entity Check: Verify an ID or fuzzy name.

💬 Pump/Group Mini: Show the risk leaderboard generated from the demo chat.

## 🧩 Architecture (Explainable by design)
The core of InfoCrux is its multi-layered, transparent architecture.

Validation Layer: Pydantic ensures data schema integrity.

Scoring Layer: Combines rules-based checks, tabular machine learning on structured data, and text-based ML on the announcement content.

Fusion: A weighted blend of the three scoring components produces the final, reliable score.

Explainability: Reason codes, corroboration checks, and text signals are rendered directly in the UI.

Auditability: The append-only Evidence Vault with SHA-256 hashes ensures a tamper-proof record.

## ✅ Mapping to SEBI’s Evaluation Criteria
Market Impact: Provides early detection of misleading disclosures, directly protecting retail investors.

Technology Stack: Leverages modern ML, NLP, and explainability frameworks with a robust audit trail.

Feasibility: The application is fully functional locally and can be easily scaled with live data feeds.

Scalability: Modular design allows for seamless integration with APIs and large datasets.

Alignment: Directly supports SEBI's mandate for market supervision and integrity.

## 📄 License
This project is for hackathon evaluation and demo use. All rights remain with the authors.

## 🧑‍💻 Maintainer
Amritha S
