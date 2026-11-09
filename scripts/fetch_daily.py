#!/usr/bin/env python3
"""NEAR daily chain series from nearblocks public API (no key): https://api.nearblocks.io/v1/charts
-> data/nearblocks_daily.csv"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
from common import get_json
d = get_json("https://api.nearblocks.io/v1/charts")["charts"]; d.sort(key=lambda r: r["date"])
F = ["date", "blocks", "txns", "active_accounts", "new_accounts", "active_contracts", "txn_fee", "near_price"]
os.makedirs("data", exist_ok=True)
with open("data/nearblocks_daily.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(F)
    for r in d:
        fee = float(r.get("txn_fee") or 0) / 1e24      # yoctoNEAR -> NEAR
        w.writerow([r["date"][:10], r.get("blocks"), r.get("txns"), r.get("active_accounts"), r.get("new_accounts"),
                    r.get("active_contracts"), round(fee, 3), r.get("near_price")])
print(f"nearblocks_daily.csv rows={len(d)} first={d[0]['date'][:10]} last={d[-1]['date'][:10]}")
# Live network stats (price, market cap) at fetch time -> data/nearblocks_stats.json
import json, datetime as dt
s = get_json("https://api.nearblocks.io/v1/stats")["stats"][0]
s["fetched_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump(s, open("data/nearblocks_stats.json", "w"), indent=1)
print(f"nearblocks_stats.json market_cap={float(s['market_cap']):,.0f} price={s['near_price']}")
