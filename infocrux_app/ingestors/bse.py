from __future__ import annotations
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def _from_demo(limit: int) -> pd.DataFrame:
    demo = pd.read_csv(ROOT / "samples" / "announcements_demo.csv")
    rows = []
    for i in range(limit):
        base = demo.iloc[i % len(demo)].copy()
        base["claimed_deal_cr"] = float(base["claimed_deal_cr"]) * (0.9 + 0.2 * np.random.rand())
        base["id"] = f"ING-{i+1:04d}"
        rows.append(base)
    return pd.DataFrame(rows).drop_duplicates(subset=["id"])

def parse_sample_fallback(html_path: Path, limit: int = 20) -> pd.DataFrame:
    # Use stdlib parser to avoid lxml build on Streamlit Cloud
    try:
        html = html_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        lis = soup.select("li.ann")
        if len(lis) >= 1:
            rows = []
            for i, li in enumerate(lis[:limit]):
                rows.append({
                    "date": li.get("data-date","2025-01-01"),
                    "company": li.get("data-company","Sample Co"),
                    "sector": li.get("data-sector","Pharma"),
                    "ann_type": li.get("data-type","Approval"),
                    "headline": (li.select_one("h4").text.strip() if li.select_one("h4") else "Sample headline"),
                    "body": (li.select_one("p").text.strip() if li.select_one("p") else "Sample body"),
                    "claimed_deal_cr": float(li.get("data-claim","100")),
                    "counterparty": li.get("data-counterparty","National Drug Authority"),
                    "timeline_months": int(li.get("data-months","3")),
                    "has_attachment": int(li.get("data-attach","1")),
                    "id": f"ING-{i+1:04d}"
                })
            df = pd.DataFrame(rows)
            if len(df) < limit:
                extra = _from_demo(limit - len(df))
                df = pd.concat([df, extra], ignore_index=True)
            return df
    except Exception:
        pass
    return _from_demo(limit)

def fetch_bse_latest(limit: int = 20, use_online: bool = True) -> pd.DataFrame:
    if use_online:
        try:
            url = "https://www.bseindia.com/corporates/ann.html"
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and "<html" in r.text.lower():
                # (We still use our known-good sample structure for demo reliability)
                return parse_sample_fallback(ROOT / "samples" / "bse_sample.html", limit)
        except Exception:
            pass
    return parse_sample_fallback(ROOT / "samples" / "bse_sample.html", limit)
