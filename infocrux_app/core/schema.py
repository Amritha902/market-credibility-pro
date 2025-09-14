
from __future__ import annotations
from typing import List, Tuple
import pandas as pd
from pydantic import BaseModel, Field

REQUIRED_COLS = [
    "date","company","sector","ann_type","headline","body",
    "claimed_deal_cr","counterparty","timeline_months","has_attachment"
]

class Announcement(BaseModel):
    date: str
    company: str
    sector: str
    ann_type: str
    headline: str
    body: str
    claimed_deal_cr: float = Field(ge=0)
    counterparty: str = ""
    timeline_months: int = Field(ge=0)
    has_attachment: int = Field(ge=0, le=1)

    @classmethod
    def from_series(cls, s: pd.Series):
        def sval(col, default=""):
            v = s.get(col, default)
            if v is None:
                return default
            try:
                if pd.isna(v):
                    return default
            except Exception:
                pass
            return v

        d = {k: sval(k, "") for k in REQUIRED_COLS}

        # strings
        for k in ["date","company","sector","ann_type","headline","body","counterparty"]:
            d[k] = str(d.get(k, "") or "").strip()

        # numbers
        try:
            d["has_attachment"] = 1 if int(float(d.get("has_attachment",0))) > 0 else 0
        except Exception:
            d["has_attachment"] = 0
        try:
            d["timeline_months"] = int(float(d.get("timeline_months",0)))
        except Exception:
            d["timeline_months"] = 0
        try:
            d["claimed_deal_cr"] = float(d.get("claimed_deal_cr",0.0))
        except Exception:
            d["claimed_deal_cr"] = 0.0

        return cls(**d)

def validate_announcements_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    errors: List[str] = []
    defaults = {
        "date":"", "company":"", "sector":"", "ann_type":"",
        "headline":"", "body":"",
        "claimed_deal_cr":0.0, "counterparty":"", "timeline_months":0, "has_attachment":0
    }
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = defaults[c]
    rows = []
    for i, row in df.iterrows():
        try:
            m = Announcement.from_series(row)
            rows.append(m.dict())
        except Exception as ve:
            errors.append(f"Row {i+1}: {ve}")
    return pd.DataFrame(rows), errors
