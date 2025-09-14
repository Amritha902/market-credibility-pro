import sys, pandas as pd
from infocrux_app.core.schema import validate_announcements_df
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_csv.py <file.csv>")
        sys.exit(1)
    df = pd.read_csv(sys.argv[1])
    cleaned, errors = validate_announcements_df(df)
    if errors:
        print("❌ Validation issues:")
        for e in errors: print("-", e)
        sys.exit(2)
    print("✅ CSV looks good. Rows:", len(cleaned))
