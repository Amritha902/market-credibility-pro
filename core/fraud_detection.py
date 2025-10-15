import re

HYPE_WORDS = [
    r"sure shot", r"guaranteed", r"x\s*returns", r"multibagger",
    r"inside info", r"firm allotment", r"pre-ipo", r"pump", r"target\s*\d+"
]

def hype_score(text: str) -> int:
    score = 0
    t = text.lower()
    for w in HYPE_WORDS:
        if re.search(w, t):
            score += 10
    return min(100, score)

def tip_verdict(text: str, ta_contradiction: bool):
    hs = hype_score(text)
    if hs >= 30 or ta_contradiction:
        return {"risk": "high", "score": max(hs, 70), "reasons": ["Hype words or TA contradiction"]}
    if hs >= 10:
        return {"risk": "medium", "score": hs, "reasons": ["Some hype indicators"]}
    return {"risk": "low", "score": hs, "reasons": ["No strong hype indicators"]}
