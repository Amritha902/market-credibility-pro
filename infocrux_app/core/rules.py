from __future__ import annotations
import pandas as pd
import numpy as np
from .config import BASE

def _baseline_merge(df: pd.DataFrame) -> pd.DataFrame:
    try:
        base = pd.read_csv(BASE / "data" / "issuer_baseline.csv")
        key = ["sector","ann_type"]
        out = df.merge(base, on=key, how="left", suffixes=("","_base"))
        out["baseline_cr"] = out["baseline_cr"].fillna(out["claimed_deal_cr"].median(skipna=True))
        return out
    except Exception:
        df = df.copy()
        df["baseline_cr"] = df["claimed_deal_cr"].median(skipna=True)
        return df

def rule_score(df: pd.DataFrame) -> pd.Series:
    X = df.copy()
    X["counterparty_named"] = X["counterparty"].fillna("").str.strip().ne("")
    try:
        reg = set(pd.read_csv(BASE / "data" / "counterparty_registry.csv")["name"].str.lower().tolist())
    except Exception:
        reg = set()
    X["registry_match"] = X["counterparty"].fillna("").str.lower().isin(reg)
    X = _baseline_merge(X)
    checks = []
    checks.append(np.where(X["counterparty_named"], 20, 0))
    checks.append(np.where(X["timeline_months"].fillna(0)>=1, 20, 0))
    checks.append(np.where(X["has_attachment"].fillna(0)>0, 20, 0))
    checks.append(np.where(X["registry_match"], 20, 0))
    ratio = (X["claimed_deal_cr"] / X["baseline_cr"].replace(0, np.nan)).clip(upper=50).fillna(1.0)
    penalty = np.clip((ratio - 2.0) / 4.0, 0, 1) * 40
    base_score = np.sum(checks, axis=0).astype(float)
    score = np.clip(base_score - penalty, 0, 100)
    return pd.Series(score, index=df.index)

def rule_reasons(row: pd.Series) -> list[str]:
    reasons = []
    if not row.get("counterparty",""): reasons.append("Counterparty missing")
    if float(row.get("timeline_months",0)) < 1: reasons.append("Timeline vague/unspecified")
    if float(row.get("has_attachment",0)) <= 0: reasons.append("No attachment")
    try:
        ratio = float(row.get("claimed_deal_cr",0)) / max(float(row.get("baseline_cr",1)), 1e-9)
        if ratio > 6.0: reasons.append("Claim >> 6× baseline")
        elif ratio > 3.0: reasons.append("Claim >> 3× baseline")
    except Exception: pass
    if not reasons: reasons.append("All corroboration checks passed")
    return reasons
