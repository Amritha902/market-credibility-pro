from __future__ import annotations
import pandas as pd
from .config import RULE_WEIGHT, TAB_WEIGHT, TXT_WEIGHT, HIGH_CUTOFF, MED_CUTOFF

def fuse_scores(rule: pd.Series, tabular: pd.Series, text: pd.Series) -> pd.Series:
    return (RULE_WEIGHT*rule + TAB_WEIGHT*(tabular*100) + TXT_WEIGHT*(text*100)).clip(0,100)

def level_from_score(s: float) -> str:
    if s < HIGH_CUTOFF: return "High"
    if s < MED_CUTOFF:  return "Medium"
    return "Low"
