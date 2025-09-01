
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class TextModel:
    def __init__(self):
        self.vect = TfidfVectorizer(min_df=1, ngram_range=(1,2), max_features=5000)
        self.clf = LogisticRegression(max_iter=2000)

    def fit(self, df: pd.DataFrame):
        X = self.vect.fit_transform((df["headline"].fillna("") + " " + df["body"].fillna("")).tolist())
        y = df["label_credible"].astype(int).values
        self.clf.fit(X, y)
        return self

    def proba(self, df: pd.DataFrame) -> np.ndarray:
        X = self.vect.transform((df["headline"].fillna("") + " " + df["body"].fillna("")).tolist())
        return self.clf.predict_proba(X)[:,1]

    def top_terms_for_row(self, row_text: str, topk: int = 8):
        X = self.vect.transform([row_text])
        coefs = self.clf.coef_[0]
        contrib = X.multiply(coefs).toarray()[0]
        idx = contrib.argsort()[::-1][:topk]
        vocab = np.array(self.vect.get_feature_names_out())
        terms = []
        for i in idx:
            if contrib[i] != 0:
                terms.append((vocab[i], float(contrib[i])))
        return terms
