
import json, time, hashlib
from pathlib import Path

LOG_FILE = Path("evidence_log.jsonl")

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def evidence_bundle(ann_obj: dict, features: dict, score_obj: dict, model_version: dict):
    raw_text = (ann_obj.get("headline","") + " " + ann_obj.get("body","")).encode("utf-8")
    bundle = {
        "announcement_id": ann_obj.get("announcement_id"),
        "ingested_at": time.time(),
        "model_version": model_version,
        "raw_hash": "sha256:"+sha256_hex(raw_text),
        "feature_hash": "sha256:"+sha256_hex(json.dumps(features, sort_keys=True).encode("utf-8")),
        "score": score_obj.get("score"),
        "level": score_obj.get("level"),
        "reasons": score_obj.get("reasons"),
        "checks": score_obj.get("checks"),
        "meta": {k: ann_obj.get(k) for k in ["date","company","sector","ann_type","counterparty"]}
    }
    return bundle

def append_log(bundle: dict):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(bundle) + "\\n")
