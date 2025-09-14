from pathlib import Path
import os

BASE = Path(__file__).resolve().parents[1]

RULE_WEIGHT = float(os.getenv("RULE_WEIGHT", 0.60))
TAB_WEIGHT  = float(os.getenv("TAB_WEIGHT", 0.20))
TXT_WEIGHT  = float(os.getenv("TXT_WEIGHT", 0.20))
HIGH_CUTOFF = float(os.getenv("HIGH_CUTOFF", 35.0))
MED_CUTOFF  = float(os.getenv("MED_CUTOFF", 70.0))

STORAGE_DIR = BASE / "storage"
STORAGE_DIR.mkdir(exist_ok=True)
EVIDENCE_LOG = STORAGE_DIR / "evidence_log.jsonl"

DATA_DIR = BASE / "data"
SAMPLES_DIR = BASE / "samples"

REQUIRED_COLS = [
    "date","company","sector","ann_type","headline","body",
    "claimed_deal_cr","counterparty","timeline_months","has_attachment",
]
