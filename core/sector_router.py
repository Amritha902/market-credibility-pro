# core/sector_router.py
import json
import os

class SectorRouter:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), "..", "config", "regulator_map.json")
        with open(config_file, "r", encoding="utf-8") as f:
            self.map = json.load(f)

    def route(self, sector: str):
        s = sector.lower()
        return self.map.get(s, {"error": f"No regulator mapping found for {s}"})
