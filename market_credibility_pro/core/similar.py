
import pandas as pd

def similar_past_cases(row: pd.Series, history: pd.DataFrame, window_days: int = 365, mag_tolerance: float=0.5):
    hist = history.copy()
    try:
        hist["date"] = pd.to_datetime(hist["date"])
    except Exception:
        pass
    mag = float(row.get("claimed_deal_cr", 0) or 0)
    sec = row.get("sector","")
    typ = row.get("ann_type","")
    mask = (hist["sector"]==sec) & (hist["ann_type"]==typ)
    if mag > 0:
        lo, hi = mag*(1-mag_tolerance), mag*(1+mag_tolerance)
        mask &= (hist["claimed_deal_cr"].astype(float).between(lo, hi) | (hist["claimed_deal_cr"]==0))
    out = hist[mask].copy()
    summary = {
        "similar_count": int(len(out)),
        "verified": int((out["status"]=="Verified").sum()),
        "pending": int((out["status"]=="Pending").sum()),
        "retracted": int((out["status"]=="Retracted").sum()),
        "median_outcome_days": float(out["outcome_days"].median()) if not out.empty else None
    }
    return out.sort_values("date", ascending=False).head(10), summary
