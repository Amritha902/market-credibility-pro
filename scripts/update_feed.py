# scripts/update_feed.py
import time, json
from ui.components import helpers

def run_update():
    print("Updating lookup.json with fresh data...")
    db = helpers.load_lookup()
    # Simulated scrape update
    db["DEMO_COMPANY"] = {"domain":"demo","ISIN":"INE123456789","valid_till":"2026-12-31"}
    with open("data/lookup.json","w",encoding="utf-8") as f:
        json.dump(db,f,indent=2)
    print("Updated lookup.json with DEMO_COMPANY")

if __name__ == "__main__":
    while True:
        run_update()
        time.sleep(3600)  # every 1h
