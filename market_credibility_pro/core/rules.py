
import pandas as pd

HEDGE = {"expects","considering","subject to","may","likely","proposed","undisclosed","withheld"}
HYPE = {"breakthrough","jackpot","upper circuit","rocket","guaranteed","multibagger","fast-track"}

def text_flags(text: str):
    t = (text or "").lower()
    hedge = sum(1 for w in HEDGE if w in t)
    hype = sum(1 for w in HYPE if w in t)
    return {"hedge_terms": hedge, "hype_terms": hype}

def rule_score(row: pd.Series, baseline: pd.Series, registry_names:set):
    reasons = []
    base = 85.0
    claim = float(row.get("claimed_deal_cr", 0) or 0.0)
    typical = float(baseline.get("typical_deal_cr", 1.0) or 1.0)
    revenue = float(baseline.get("fy_revenue_cr", 1.0) or 1.0)

    txt = f"{row.get('headline','')} {row.get('body','')}"
    tf = text_flags(txt)
    counterparty_present = bool(str(row.get("counterparty","")).strip())
    has_timeline = float(row.get("timeline_months",0) or 0) > 0
    has_attachment = bool(int(row.get("has_attachment",0) or 0))
    financial_disclosed = claim > 0
    registry_match = (str(row.get("counterparty","")).strip() in registry_names) if counterparty_present else False

    penalty = 0.0
    if financial_disclosed:
        ratio_typical = claim / max(typical, 1.0)
        ratio_revenue = claim / max(revenue, 1.0)
        if ratio_typical > 6:
            penalty += 0.35; reasons.append("Claim >> historical median deal size")
        elif ratio_typical > 3:
            penalty += 0.20; reasons.append("Claim >> typical deal size")
        if ratio_revenue > 0.30:
            penalty += 0.25; reasons.append("Claim large vs annual revenue")
    else:
        penalty += 0.10; reasons.append("Financial details undisclosed")

    if not counterparty_present:
        penalty += 0.12; reasons.append("Counterparty not named")
    if not has_timeline:
        penalty += 0.08; reasons.append("Timeline not specified")
    if not has_attachment:
        penalty += 0.05; reasons.append("No attachment/document")

    if tf["hedge_terms"] > 0:
        penalty += min(0.15, 0.04*tf["hedge_terms"])
        reasons.append(f"Hedging language ({tf['hedge_terms']})")
    if tf["hype_terms"] > 0:
        penalty += min(0.12, 0.04*tf["hype_terms"])
        reasons.append(f"Hype language ({tf['hype_terms']})")

    if counterparty_present and not registry_match:
        penalty += 0.08; reasons.append("No corroboration for counterparty in registry")

    score = max(0.0, min(100.0, base - 100.0*penalty))
    level = "Low" if score>70 else ("Medium" if score>=35 else "High")
    checks = {
        "counterparty_named": counterparty_present,
        "timeline_specified": has_timeline,
        "financial_disclosed": financial_disclosed,
        "attachment_present": has_attachment,
        "registry_match": registry_match
    }
    return score, level, reasons, checks
