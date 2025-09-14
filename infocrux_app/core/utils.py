from __future__ import annotations
from pathlib import Path
import hashlib
import pandas as pd
from .config import BASE

def here(*parts: str) -> Path:
    return BASE.joinpath(*parts)

def sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()

def badge_for_level(level: str) -> str:
    color = {"High":"#d93025","Medium":"#e09f1f","Low":"#1f8f2e"}.get(level,"#666")
    return f"<span style='background:{color};color:white;padding:3px 10px;border-radius:12px;font-weight:600'>{level}</span>"

def load_csv(rel: str):
    p = here(rel)
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.read_csv(p, engine='python', on_bad_lines='skip')
