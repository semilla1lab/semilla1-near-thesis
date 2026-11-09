#!/usr/bin/env python3
"""NEAR Intents daily swap volume, fees and NEAR-captured revenue from DefiLlama public API (no key).
Sources: https://api.llama.fi/summary/dexs/near-intents , https://api.llama.fi/summary/fees/near-intents
-> data/intents_daily.csv"""
import os, sys, csv, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from common import get_json
B = "https://api.llama.fi/summary/"
series = {"volume_usd": B + "dexs/near-intents?dataType=dailyVolume",
          "fees_usd": B + "fees/near-intents?dataType=dailyFees",
          "revenue_usd": B + "fees/near-intents?dataType=dailyRevenue",
          "holders_revenue_usd": B + "fees/near-intents?dataType=dailyHoldersRevenue"}
rows = {}
for k, u in series.items():
    for ts, v in get_json(u).get("totalDataChart", []):
        d = dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")
        rows.setdefault(d, {})[k] = v
os.makedirs("data", exist_ok=True)
with open("data/intents_daily.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date"] + list(series))
    for d in sorted(rows): w.writerow([d] + [rows[d].get(k, "") for k in series])
print(f"intents_daily.csv rows={len(rows)} first={min(rows)} last={max(rows)}")
