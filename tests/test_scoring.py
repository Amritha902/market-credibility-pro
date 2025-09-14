import pandas as pd
from infocrux_app.core.rules import rule_score
from infocrux_app.core.fusion import fuse_scores

def test_scoring_runs():
    df = pd.DataFrame([{
        "date":"2025-08-18","company":"X","sector":"IT","ann_type":"Partnership",
        "headline":"h","body":"b","claimed_deal_cr":100,"counterparty":"Y","timeline_months":3,"has_attachment":1
    }])
    r = rule_score(df)
    fused = fuse_scores(r, r*0 + 0.8, r*0 + 0.9)
    assert 0 <= fused.iloc[0] <= 100
