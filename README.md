# Semilla1 NEAR Thesis — from transactions to Intents fees

**Track:** `thesis` (Investment Thesis) · **Built at NEAR HACKATHON** (work started 2026-11-04, inside the window) · **License:** MIT

**TL;DR**
1. A long-term thesis for NEAR backed only by public, keyless data that anyone can re-run with `./run_all.sh` (bash + python3 stdlib, no API key, no wallet).
2. Finding: raw base-layer activity fell hard (tx/day −85% YoY), while **NEAR Intents** settlement grew (+60% YoY volume) and its fees are now **~35× the L1 gas fees**; part of those fees funds a NEAR buyback since 2026-02-23.
3. The thesis is falsifiable: `THESIS.md` lists the exact metrics and thresholds that would kill it, and every number is regenerated into `data/findings.json`.

## What problem this solves
Most NEAR "theses" quote one headline number (transactions, TVL or price). Transaction counts on NEAR are dominated by a few high-frequency apps and change by an order of magnitude in a year, so they say little about value capture. This repo answers one question with re-runnable evidence: **where does NEAR actually earn money today, and is that growing?** It also shows how to check the core chain metric yourself instead of trusting an indexer.

## Try it (do X → see Y)
| Do | See |
|---|---|
| `git clone https://github.com/semilla1lab/semilla1-near-thesis && cd semilla1-near-thesis && ./run_all.sh --quick` | ~10-15 min (public RPC). Prints row counts of the two daily series, a block-sample estimate of yesterday's tx/day with a 95% CI, and the findings table. |
| Open `docs/REPORT.md` (or `docs/index.html` in a browser) | The 15-row findings table and 4 charts (tx/day, Intents volume, Intents fees, L1 gas fees), all from `data/findings.json`. |
| `DAY=2026-11-08 ./run_all.sh` | Reproduces the exact independent check used in THESIS.md: 1200 random blocks of 2026-11-08 (seed 42, ~25-35 min) → 596,027 tx/day (95% CI 567,878–624,175) vs nearblocks 609,504. |
| `python3 scripts/sample_day.py 2026-11-07 200 42` | A second day (committed as `data/sample_2026-11-07.json`): 724,687 (95% CI 643,834–805,540) vs nearblocks 682,432 — inside again. |
| `python3 scripts/window_noise.py 2026-11-08` | Why short samples mislead: 20-block windows of the same day range p10 2.7 → p90 10.5 tx/s (day average 7.05). |
| Read `THESIS.md` | The thesis, the evidence, risks, and kill criteria. |
| Watch `docs/demo.mp4` (71 s) | Problem → real run output → charts → onchain audit → kill criteria. |

Snapshot committed in `data/` is through **2026-11-08 UTC**. Re-running refreshes it; numbers in `THESIS.md` are the snapshot values and `docs/REPORT.md` always shows the latest run.

## How NEAR fits in
- **Onchain data straight from NEAR:** `scripts/sample_day.py` reads blocks and chunks over public NEAR JSON-RPC (archival) and counts signed transactions and transactions addressed to `intents.near`, the NEAR Intents contract. No indexer trust needed for the core count.
- **NEAR Intents** is the subject of the thesis: cross-chain swaps settled on NEAR, with fees partly captured by NEAR and used for buybacks.
- **Indexers as cross-checks:** nearblocks daily charts (chain) and DefiLlama (Intents volume/fees/revenue).

## Data sources (all public, no key)
| Source | Endpoint | Used for |
|---|---|---|
| NEAR archival JSON-RPC (FastNEAR, listed at docs.near.org/api/rpc/providers) | `https://archival-rpc.mainnet.fastnear.com` methods `block`, `chunk` | Independent tx/day estimate, intents.near share, receipts |
| nearblocks | `https://api.nearblocks.io/v1/charts`, `/v1/stats` | Daily tx, blocks, active/new accounts, gas fees (NEAR), price, market cap |
| DefiLlama | `https://api.llama.fi/summary/dexs/near-intents`, `/summary/fees/near-intents` (`dailyFees`, `dailyRevenue`, `dailyHoldersRevenue`) | Intents volume, gross fees, NEAR-captured revenue, buyback |

## Repo map
```
run_all.sh                 one command: fetch -> sample -> build
scripts/common.py          HTTP + JSON-RPC helpers (stdlib)
scripts/fetch_daily.py     nearblocks -> data/nearblocks_daily.csv, data/nearblocks_stats.json
scripts/fetch_intents.py   DefiLlama -> data/intents_daily.csv
scripts/sample_day.py      random-block sample of one UTC day -> data/sample_<day>.json
scripts/window_noise.py    20-block window spread -> data/window_noise_<day>.json
scripts/build.py           -> data/findings.json, docs/REPORT.md, docs/index.html
THESIS.md                  the thesis (human + machine readable)
```

## Limitations (honest)
- Intents volume/fees/revenue come from DefiLlama's adapter, not from our own decoding of `intents.near`; we cross-check only the transaction share onchain.
- The block sample measures *transactions sent to* `intents.near`, not the USD value they settle.
- Revenue run-rate is a 30-day extrapolation; market cap is read live from nearblocks at fetch time.
- This is research, not financial advice.

## Disclosure (Q-015) — other project by the same team
The same team also submitted **Semilla1 Guard** (tracks `security`, `agents`): https://github.com/semilla1lab/semilla1-guard-near — an on-chain spending-policy vault for AI agents. The two projects are independent: different problem, different code, no shared files.

## Libraries / baseline (Q-005)
Python 3 standard library only. No templates. Two exploratory scripts written on 2026-11-04 were rewritten into `scripts/`.
