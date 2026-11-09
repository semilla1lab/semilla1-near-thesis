#!/usr/bin/env python3
"""Why a 20-block sample can't predict a day: read K windows of W consecutive blocks at random
points of one UTC day and show how much tx/s swings between windows.
Usage: python3 scripts/window_noise.py 2026-11-08 [K=30] [W=20] [seed=7]  -> data/window_noise_<date>.json"""
import sys, os, json, random, statistics as st
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from common import rpc
EMPTY = "11111111111111111111111111111111"
day = sys.argv[1]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 30
W = int(sys.argv[3]) if len(sys.argv) > 3 else 20; SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 7
s = json.load(open(f"data/sample_{day}.json"))["summary"]; h0, h1 = s["height_range"]
starts = sorted(random.Random(SEED).sample(range(h0, h1 - 200), K))
def blk(h):
    b, _ = rpc("block", {"block_id": h})
    if not b: return None
    tx = 0
    for c in b["chunks"]:
        if c["height_included"] != h or c["tx_root"] == EMPTY: continue
        ch, _ = rpc("chunk", {"chunk_id": c["chunk_hash"]}); tx += len((ch or {}).get("transactions", []))
    return b["header"]["timestamp"], tx
def window(start):
    got = []; h = start
    while len(got) < W + 1:
        r = blk(h); h += 1
        if r: got.append(r)
    # W intervals between W+1 blocks; count tx of the last W blocks (exact, no off-by-one)
    secs = (got[-1][0] - got[0][0]) / 1e9
    return {"start": start, "tx": sum(t for _, t in got[1:]), "secs": round(secs, 2), "tx_per_s": round(sum(t for _, t in got[1:]) / secs, 2)}
with ThreadPoolExecutor(6) as ex: ws = list(ex.map(window, starts))
r = [w["tx_per_s"] for w in ws]; q = st.quantiles(r, n=10)
out = {"day_utc": day, "windows": K, "blocks_per_window": W, "tx_per_s_min": min(r), "tx_per_s_p10": round(q[0], 2),
       "tx_per_s_median": round(st.median(r), 2), "tx_per_s_p90": round(q[-1], 2), "tx_per_s_max": max(r),
       "implied_tx_per_day_range_p10_p90": [round(q[0] * 86400), round(q[-1] * 86400)]}
json.dump({"summary": out, "windows": ws}, open(f"data/window_noise_{day}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
