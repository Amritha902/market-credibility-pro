
import re, pandas as pd, numpy as np

PUMP_TERMS = {"load up","upper circuit","target","multibagger","guaranteed","VIP","premium","DM","join telegram","crypto"}

def parse_symbols(text: str):
    if not isinstance(text, str): return []
    return [w for w in re.findall(r"\b[A-Z]{3,}\b", text) if w.isalpha()]

def score_group(chat_df: pd.DataFrame) -> pd.DataFrame:
    df = chat_df.copy()
    df["symbols"] = df["text"].apply(parse_symbols)
    df["pump_terms"] = df["text"].str.lower().apply(lambda t: sum(1 for k in PUMP_TERMS if k.lower() in (t or "")))
    exploded = df.explode("symbols")
    counts = exploded.groupby("symbols")["text"].count().rename("mentions").reset_index()
    pump_hits = df["pump_terms"].sum()
    counts["pump_risk"] = np.clip((counts["mentions"]/max(1, counts["mentions"].max()))*0.6 + (pump_hits/ max(1, len(df))) * 0.4, 0, 1)
    counts["pump_risk"] = counts["pump_risk"].round(2)
    return counts.sort_values("pump_risk", ascending=False)
