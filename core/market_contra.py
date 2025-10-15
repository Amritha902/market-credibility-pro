# core/market_contra.py
import numpy as np

def moving_average(data, window):
    return np.convolve(data, np.ones(window), "valid") / window

def compute_rsi(data, period=14):
    deltas = np.diff(data)
    if len(deltas) < period:
        return 50
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs)
    return rsi

def contradiction_score(prices, announcement_type="positive"):
    ma20 = moving_average(prices, 20)[-1] if len(prices) >= 20 else np.mean(prices)
    rsi = compute_rsi(prices) if len(prices) > 15 else 50
    last_price = prices[-1]
    score = 0
    if announcement_type=="positive" and last_price < ma20:
        score += 1
    if announcement_type=="negative" and last_price > ma20:
        score += 1
    if (rsi > 70 and announcement_type=="positive") or (rsi < 30 and announcement_type=="negative"):
        score += 1
    return {"ma20": float(ma20), "rsi": float(rsi), "contradiction_score": score}
