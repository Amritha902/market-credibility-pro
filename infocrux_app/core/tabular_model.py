from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

FEATURES = ["claimed_deal_cr","timeline_months","has_attachment","text_len","has_counterparty"]

class ConstProb:
    def __init__(self, p: float): self.p = float(p)
    def predict_proba(self, X):
        n = len(X) if hasattr(X, "__len__") else 1
        return np.column_stack([np.full(n, 1-self.p), np.full(n, self.p)])

def train_tabular(df: pd.DataFrame):
    X = df.copy()
    X["text_len"] = (X["headline"].fillna("").str.len() + X["body"].fillna("").str.len()).astype(float)
    X["has_counterparty"] = X["counterparty"].fillna("").str.strip().ne("").astype(float)
    Xf = X[FEATURES].astype(float).values
    y = ((X["has_counterparty"]>0) & (X["timeline_months"].fillna(0)>=1) & (X["has_attachment"]>0)).astype(int).values
    if len(np.unique(y)) < 2:
        return ConstProb(float(y[0]) if len(y)>0 else 0.5)
    clf = Pipeline([("scaler", StandardScaler()), ("lr", LogisticRegression(max_iter=1000))])
    clf.fit(Xf, y)
    return clf

def predict_tabular(model, df: pd.DataFrame) -> pd.Series:
    X = df.copy()
    X["text_len"] = (X["headline"].fillna("").str.len() + X["body"].fillna("").str.len()).astype(float)
    X["has_counterparty"] = X["counterparty"].fillna("").str.strip().ne("").astype(float)
    Xf = X[FEATURES].astype(float).values
    proba = model.predict_proba(Xf)[:,1]
    return pd.Series(proba, index=df.index)
