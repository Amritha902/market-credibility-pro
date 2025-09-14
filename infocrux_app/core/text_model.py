from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

RISK_TERMS = ["breakthrough","guaranteed","assured","fast-track","nod","rumor","leak","exclusive","unprecedented","firm allotment"]

class ConstProb:
    def __init__(self, p: float): self.p = float(p)
    def predict_proba(self, X):
        n = len(X) if hasattr(X, "__len__") else 1
        return np.column_stack([np.full(n, 1-self.p), np.full(n, self.p)])

def train_text(df: pd.DataFrame):
    txt = (df["headline"].fillna("") + " " + df["body"].fillna("")).astype(str)
    y = txt.str.lower().apply(lambda s: sum(t in s for t in RISK_TERMS) >= 2).astype(int)
    y = 1 - y
    if len(np.unique(y)) < 2:
        return ConstProb(float(y.iloc[0]) if len(y)>0 else 0.5)
    pipe = Pipeline([("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1,2))), ("lr", LogisticRegression(max_iter=1000))])
    pipe.fit(txt, y)
    return pipe

def predict_text(model, df: pd.DataFrame):
    txt = (df["headline"].fillna("") + " " + df["body"].fillna("")).astype(str)
    proba = model.predict_proba(txt)[:,1]
    return pd.Series(proba, index=df.index)

def text_signals(row: pd.Series) -> list[str]:
    s = (str(row.get("headline","")) + " " + str(row.get("body",""))).lower()
    hits = [t for t in RISK_TERMS if t in s]
    return hits[:12]
