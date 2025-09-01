
import numpy as np

def fuse(rule_score, tabular_proba, text_proba, w=(0.5, 0.3, 0.2)):
    rs = np.asarray(rule_score) / 100.0
    tp = np.asarray(tabular_proba)
    xp = np.asarray(text_proba)
    fused = w[0]*rs + w[1]*tp + w[2]*xp
    return (fused * 100.0).clip(0, 100)

def level(score):
    return "Low" if score>70 else ("Medium" if score>=35 else "High")
