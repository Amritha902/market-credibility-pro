# core/social_signals.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

TRAIN_TEXTS = [
    "pump huge buy now",
    "this is a scam",
    "fake news about company",
    "official regulatory filing",
    "results announced genuine",
    "insider tip buy",
    "sell off rumor",
    "company confirms acquisition"
]
TRAIN_LABELS = [0, 0, 0, 1, 1, 0, 0, 1]  # 1 = legit, 0 = suspicious

class SocialSignalClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2))
        X = self.vectorizer.fit_transform(TRAIN_TEXTS)
        self.clf = LogisticRegression()
        self.clf.fit(X, TRAIN_LABELS)

    def classify(self, text: str, threshold=0.5):
        X = self.vectorizer.transform([text])
        prob = self.clf.predict_proba(X)[0,1]
        return {
            "text": text,
            "score": float(prob),
            "label": "legit" if prob >= threshold else "suspicious"
        }
