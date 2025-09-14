import pandas as pd
from infocrux_app.core.schema import validate_announcements_df

def test_validate_basic():
    df = pd.DataFrame([{
        "date":"2025-08-18","company":"X","sector":"IT","ann_type":"Partnership",
        "headline":"h","body":"b","claimed_deal_cr":100,"counterparty":"Y","timeline_months":3,"has_attachment":1
    }])
    cleaned, errors = validate_announcements_df(df)
    assert errors == []
    assert len(cleaned) == 1
