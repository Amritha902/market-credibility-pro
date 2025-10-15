# core/anomaly_detector.py
import pandas as pd
import numpy as np

class AnomalyDetector:
    """
    Detect anomalies by comparing new filings vs historical filings.
    Example keys: {"revenue": 1000, "profit": 200, "eps": 10}
    """

    def detect_numeric_anomalies(self, series, threshold=0.2):
        s = pd.Series(series).dropna()
        if len(s) < 2:
            return {"anomaly": False, "latest": s.iloc[-1] if not s.empty else None}
        mean = s[:-1].mean()
        latest = s.iloc[-1]
        deviation = (latest - mean) / mean if mean else 0
        return {
            "latest": latest,
            "mean": mean,
            "deviation": deviation,
            "anomaly": abs(deviation) > threshold
        }

    def compare_filing(self, new_filing: dict, historical: list):
        anomalies = {}
        for key in ["revenue", "profit", "eps"]:
            if key in new_filing:
                series = [h.get(key) for h in historical if h.get(key) is not None]
                series.append(new_filing[key])
                anomalies[key] = self.detect_numeric_anomalies(series)
        return anomalies
