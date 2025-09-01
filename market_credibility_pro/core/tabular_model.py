
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

FEATURES = [
    "claimed_over_typical",
    "claimed_over_revenue",
    "has_timeline",
    "has_attachment",
    "financial_disclosed",
    "hedge_terms",
    "hype_terms",
    "registry_match"
]

def build_features(df: pd.DataFrame, baseline: pd.DataFrame, registry_names:set) -> pd.DataFrame:
    out = df.copy()
    out = out.merge(baseline[["company","fy_revenue_cr","typical_deal_cr"]], on="company", how="left")
    out["claimed_over_typical"] = (out["claimed_deal_cr"].fillna(0) / out["typical_deal_cr"].replace(0,1)).clip(0, 20)
    out["claimed_over_revenue"] = (out["claimed_deal_cr"].fillna(0) / out["fy_revenue_cr"].replace(0,1)).clip(0, 1)
    out["has_timeline"] = (out["timeline_months"].fillna(0) > 0).astype(int)
    out["has_attachment"] = out["has_attachment"].fillna(0).astype(int)
    out["financial_disclosed"] = (out["claimed_deal_cr"].fillna(0) > 0).astype(int)
    def count_terms(text, terms):
        t = (text or "").lower()
        return sum(1 for w in terms if w in t)
    HEDGE = {"expects","considering","subject to","may","likely","proposed","undisclosed","withheld"}
    HYPE = {"breakthrough","jackpot","upper circuit","rocket","guaranteed","multibagger","fast-track"}
    out["hedge_terms"] = (out["headline"].fillna("") + " " + out["body"].fillna("")).apply(lambda s: count_terms(s, HEDGE))
    out["hype_terms"] = (out["headline"].fillna("") + " " + out["body"].fillna("")).apply(lambda s: count_terms(s, HYPE))
    out["registry_match"] = out["counterparty"].fillna("").apply(lambda x: 1 if x.strip() in registry_names else 0)
    return out

def fit_model(train_df: pd.DataFrame):
    X = train_df[FEATURES].values
    y = train_df["label_credible"].astype(int).values
    model = LogisticRegression(max_iter=2000)
    model.fit(X, y)
    return model

def predict_proba(model, df_feat: pd.DataFrame) -> np.ndarray:
    X = df_feat[FEATURES].values
    proba = model.predict_proba(X)[:,1]
    return proba
