# 📊 Credibility Pro — SEBI Hackathon Submission

**Theme:** Fraud Prevention — Protecting retail investors from misleading or fraudulent corporate announcements.  

---

## 🚨 Problem Statement
Fraudsters and some listed companies exploit **misleading corporate announcements** to manipulate markets:
- Vague or exaggerated disclosures (e.g., "breakthrough approval", "large project win")  
- Fabricated announcements circulated through media/social platforms  
- Investors misled → losses, pump-and-dump cycles, erosion of trust  

---

## ✅ Our Solution
We built **Announcement Credibility Pro**:  
An AI-powered system that **analyzes announcements in real-time**, assigns a **Credibility Score (0–100)**, and provides **audit-ready explanations and evidence** for regulators, analysts, and investors.  

---

## 🔑 How We Address the Hackathon Criteria
- **Market Impact:** Protects retail investors, restores market integrity, empowers SEBI’s supervision.  
- **Technology Stack:** AI/ML, NLP, explainable scoring, hashing for audit trail, Streamlit dashboard.  
- **Feasibility:** Works today with CSV uploads & BSE ingestion; deployable with real feeds tomorrow.  
- **Scalability:** Extends across all listed companies and disclosures; modular ingestion + scoring.  
- **Alignment with SEBI’s Mandate:** Directly tackles **investor protection**, **market development**, and **supervision**.  

---

## ✨ Key Features
### 🧠 Credibility Scoring Engine
- Rule-based checks + Tabular ML + Text ML (TF-IDF)  
- Fusion model → **High / Medium / Low Risk classification**  

### 🔍 Explainable Outputs
- **Reason Codes** (e.g., "Claim >> 6× historical median")  
- ✅/❌ **Corroboration signals** (counterparty, timeline, attachment, registry match)  
- **Top NLP terms** influencing credibility  

### 🗂️ Similar Past Cases
- Detects announcements of **similar type & magnitude**  
- Shows outcomes: Verified / Pending / Retracted  
- Builds **institutional memory** for regulators  

### 📜 Evidence Vault
- Auto-generates **evidence.json** with:  
  - Hash of raw text + features  
  - Final score + reasons + checks  
  - Model versioning  
- Append-only `evidence_log.jsonl` for audit trail  

### 📊 Regulator Dashboard
- **Triage** of lowest-credibility announcements  
- **Heatmap** (sector × announcement type) for risk concentration  

### 💬 Pump/Group Mini Surveillance
- Analyzes chat-like data (WhatsApp/Telegram groups)  
- Flags potential **pump-and-dump campaigns**  

### 🔗 BSE Ingestion Module
- Fetches recent announcements from BSE portal (demo-safe fallback HTML)  
- Converts them automatically into our scoring schema  
- Demonstrates **real-world deployability**  

---

## 👩‍💼 Intended Users
- **Regulators (SEBI, Exchanges):** Detect misleading announcements quickly  
- **Media & Analysts:** Validate credibility before amplifying news  
- **Retail Investors (future roadmap):** Simplified “credibility badge” on disclosures  

---

## 🌍 Impact
- Shields millions of investors from fraud  
- Reduces pump-and-dump schemes  
- Builds **trust in Indian securities markets**  
- Can evolve into a **supervisory system at SEBI** with minimal integration  

---

## 🛠️ Technology Stack
- **Python** (Pandas, scikit-learn, NumPy)  
- **NLP:** TF-IDF, language risk lexicons  
- **AI/ML Models:** Logistic Regression (tabular + text)  
- **Frontend:** Streamlit  
- **Data ingestion:** Requests + BeautifulSoup (BSE)  
- **Integrity:** SHA-256 hashing  

---
<img width="1874" height="816" alt="image" src="https://github.com/user-attachments/assets/f8891546-5884-4d54-8b01-bf7eaa949548" />
<img width="1877" height="778" alt="image" src="https://github.com/user-attachments/assets/643ddc9e-d063-4e6f-bc8c-8f1018e05ee7" />
<img width="1895" height="852" alt="image" src="https://github.com/user-attachments/assets/93c55ddb-6777-4f53-a70a-a23eb987aec4" />
<img width="1841" height="755" alt="image" src="https://github.com/user-attachments/assets/e1040acf-281b-4945-947b-0f6c8c04d3d3" />
<img width="1839" height="745" alt="image" src="https://github.com/user-attachments/assets/c0ef9cf4-0dcd-4593-aca3-7cb673a233e3" />



## ⚙️ How to Run
```bash
# Clone repo
git clone https://github.com/Amritha902/market-credibility-pro.git
cd market-credibility-pro

# Setup environment
python -m venv .venv
.venv\Scripts\activate  # on Windows

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
