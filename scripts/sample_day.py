#!/usr/bin/env python3
"""Independent check of NEAR daily transaction count, straight from the chain.

Picks N random block heights inside one UTC day (fixed seed -> reproducible), reads every
chunk that was *newly included* in that block via public archival RPC, and counts signed
transactions (not receipts). Daily estimate = mean tx per produced block x blocks produced.
Also measures the share of transactions whose receiver is intents.near (NEAR Intents).

Usage: python3 scripts/sample_day.py 2026-11-08 [N=400] [seed=42]
Writes data/sample_<date>.json. Stdlib only, no key.
"""
import sys, os, json, random, math, datetime as dt
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from common import rpc

EMPTY = "11111111111111111111111111111111"
day = sys.argv[1] if len(sys.argv) > 1 else (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 400
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 42
t0 = dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc)
T0, T1 = int(t0.timestamp() * 1e9), int((t0 + dt.timedelta(days=1)).timestamp() * 1e9)

def block_at_or_after(h):
    for k in range(50):                      # skip heights with no block
        b, err = rpc("block", {"block_id": h + k})
        if b: return b
    raise RuntimeError(f"no block near {h}")

def first_height_ge(ts):
    """Binary search for the first block with timestamp >= ts."""
    tip, _ = rpc("block", {"finality": "final"})
    lo, hi = 9820210, tip["header"]["height"]      # 9820210 = mainnet genesis height
    while hi - lo > 1:
        mid = (lo + hi) // 2
        b = block_at_or_after(mid)
        if b["header"]["timestamp"] >= ts: hi = mid
        else: lo = mid
    return hi

h0, h1 = first_height_ge(T0), first_height_ge(T1)
rng = random.Random(SEED)
heights = sorted(rng.sample(range(h0, h1), N))

def read(h):
    b, err = rpc("block", {"block_id": h})
    if not b: return {"h": h, "produced": False}
    tx = intents = receipts = 0; repeated = 0
    for c in b["chunks"]:
        if c["height_included"] != h:          # chunk re-carried from an earlier block: not new
            repeated += 1; continue
        ch, _ = rpc("chunk", {"chunk_id": c["chunk_hash"]})   # read every new chunk (receipts live there too)
        receipts += len((ch or {}).get("receipts", []))
        for t in (ch or {}).get("transactions", []):
            tx += 1; intents += t["receiver_id"] == "intents.near"
    return {"h": h, "produced": True, "tx": tx, "intents": intents, "receipts": receipts, "repeated_chunks": repeated}

with ThreadPoolExecutor(8) as ex:
    rows = list(ex.map(read, heights))
prod = [r for r in rows if r["produced"]]
p_frac = len(prod) / len(rows)
blocks_est = p_frac * (h1 - h0)
xs = [r["tx"] for r in prod]
m = sum(xs) / len(xs); sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
se = sd / math.sqrt(len(xs))
tot_tx = sum(xs); tot_int = sum(r["intents"] for r in prod)
out = {
    "day_utc": day, "method": "random produced-block sample, newly included chunks only, signed transactions",
    "rpc": "https://archival-rpc.mainnet.fastnear.com", "seed": SEED, "heights_sampled": N,
    "height_range": [h0, h1], "blocks_produced_est": round(blocks_est),
    "mean_tx_per_block": round(m, 3), "sd_tx_per_block": round(sd, 3),
    "tx_per_day_est": round(m * blocks_est), "tx_per_day_95ci": [round((m - 1.96 * se) * blocks_est), round((m + 1.96 * se) * blocks_est)],
    "intents_share_of_tx": round(tot_int / tot_tx, 4) if tot_tx else None,
    "intents_tx_per_day_est": round(tot_int / tot_tx * m * blocks_est) if tot_tx else None,
    "receipts_per_day_est": round(sum(r["receipts"] for r in prod) / len(prod) * blocks_est),
    "receipts_per_tx": round(sum(r["receipts"] for r in prod) / tot_tx, 2) if tot_tx else None,
    "repeated_chunk_headers_seen": sum(r.get("repeated_chunks", 0) for r in prod),
}
os.makedirs("data", exist_ok=True)
json.dump({"summary": out, "rows": rows}, open(f"data/sample_{day}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
