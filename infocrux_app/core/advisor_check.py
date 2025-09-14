from __future__ import annotations
import pandas as pd
from rapidfuzz import fuzz, process
from pathlib import Path

def load_registry(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["name_norm"] = df["name"].str.lower().str.strip()
    df["text_id"] = df["text_id"].astype(str)
    return df

def check_entity(df: pd.DataFrame, query_name: str, reg_id: str | None = None, top_k: int = 3):
    name = (query_name or "").lower().strip()
    rid = (reg_id or "").strip()
    exact = None
    if rid:
        m = df[df["text_id"].str.lower()==rid.lower()]
        if not m.empty:
            exact = m.iloc[0].to_dict()
    choices = dict(zip(df["name_norm"], df.index))
    results = process.extract(name, list(choices.keys()), scorer=fuzz.token_sort_ratio, limit=top_k)
    fuzzy = []
    for nm, score, _ in results:
        row = df.loc[choices[nm]].to_dict()
        row["fuzzy_score"] = int(score)
        fuzzy.append(row)
    return exact, fuzzy
