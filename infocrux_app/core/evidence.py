from __future__ import annotations
from .utils import here, sha256_bytes
from .fusion import level_from_score
from .config import EVIDENCE_LOG
import json, time

LOG_FILE = EVIDENCE_LOG

def evidence_bundle(row: dict, score: float, reasons: list[str], checks: dict, model_version: dict) -> dict:
    raw = json.dumps(row, sort_keys=True).encode()
    feats = json.dumps(checks, sort_keys=True).encode()
    return {
        "announcement_id": row.get("id",""),
        "ingested_at": time.time(),
        "model_version": model_version,
        "raw_hash": sha256_bytes(raw),
        "feature_hash": sha256_bytes(feats),
        "score": round(float(score),2),
        "level": level_from_score(score),
        "reasons": reasons,
        "checks": checks,
        "meta": {
            "date": row.get("date",""),
            "company": row.get("company",""),
            "sector": row.get("sector",""),
            "ann_type": row.get("ann_type",""),
            "counterparty": row.get("counterparty",""),
        },
    }

def append_log(bundle: dict):
    line = json.dumps(bundle, ensure_ascii=False)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
