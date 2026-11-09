# THESIS: NEAR's value is moving from L1 transactions to Intents settlement fees

*Semilla1 Lab · NEAR HACKATHON, track `thesis` · data snapshot through 2026-11-08 UTC · every number below is in `data/findings.json` (regenerate: `./run_all.sh`)*

## 1. Claim (one paragraph)
Over a multi-year horizon, the case for NEAR should not rest on transaction counts or accounts, which have collapsed from their 2025 bot-driven peak. It rests on **NEAR Intents**: a cross-chain settlement layer whose fees already dwarf NEAR's own L1 gas fees, and whose NEAR-captured share funds open-market NEAR buybacks. If Intents fees and the captured share keep growing while L1 activity stays flat, NEAR behaves less like a "busy L1" and more like a **fee-generating settlement network**. The thesis is judged on the evidence below, and section 6 states what would prove it wrong.

## 2. Evidence
All windows: last 30 days = 2026-10-10..2026-11-08 UTC; "YoY" = same 30 days one year earlier (2025-10-10..2025-11-08).

### 2a. Base layer: activity is down a lot (nearblocks `/v1/charts`)
| Metric | Last 30d avg | vs previous 30d | YoY |
|---|---|---|---|
| Signed transactions / day | 661,021 | −22.4% | −85.2% (from 4,465,527) |
| Active accounts / day | 57,527 | −24.3% | −78.2% |
| New accounts / day | 9,429 | −20.8% | −95.8% |
| L1 gas fees (total, 30d) | 34,842 NEAR ≈ **$165,810** | — | fees in NEAR −64.9% |

The 30-day average of tx/day peaked at 8,296,230 on 2025-01-01. Raw activity on NEAR has been dominated by a few high-frequency apps; it is not a reliable value signal.

### 2b. NEAR Intents: settlement is growing (DefiLlama `near-intents`)
| Metric | Last 30d | vs previous 30d | YoY |
|---|---|---|---|
| Swap volume | **$3.71B** | −22.0% | **+59.9%** (from $2.32B) |
| Gross fees | **$5.78M** | −27.8% | +54.4% |
| NEAR-captured revenue | **$1.86M** | −13.0% | **+339%** (from $0.42M) |

- Cumulative Intents volume since 2024-12-10: **$37.0B**.
- Take rate (fees / volume, 30d): **15.56 bps**. NEAR captures **32.1%** of gross fees.
- **Intents gross fees are 34.9× NEAR's L1 gas fees** over the same 30 days ($5.78M vs $0.17M).
- Since 2026-02-23 the captured revenue buys NEAR on the open market (DefiLlama methodology: *"NEAR's captured Intents revenue is used to buy back $NEAR on the open market (not burned)"*): **$7.89M** so far.
- 30-day revenue run-rate: **$22.6M/yr = 0.47%** of NEAR market cap ($4.78B, nearblocks `/v1/stats`, read 2026-11-09 22:44 UTC).
- The last 30 days are *down* vs the 30 before (September 2026 was the record month, $4.80B volume). The thesis is about the multi-month trend, not one month.

### 2c. Onchain cross-check: we counted it ourselves (NEAR archival RPC)
`scripts/sample_day.py 2026-11-08 1200 42` reads 1,200 random block heights of 2026-11-08 UTC (seed 42), every newly included chunk, and counts signed transactions:
- Blocks produced that day: **151,116** estimated vs **151,113** in nearblocks (−0.002%).
- Transactions: **596,027/day (95% CI 567,878–624,175)** vs nearblocks **609,504** → nearblocks is inside our interval (−2.2%).
- **17.4%** of all signed transactions on NEAR that day were sent to `intents.near` (~104,018/day).
- Second day, quick mode (`scripts/sample_day.py 2026-11-07 200 42`): **724,687/day (95% CI 643,834–805,540)** vs nearblocks **682,432** → inside again; 14.2% to `intents.near`.
- Receipts (internal cross-shard messages a transaction spawns): ~3,085,915/day, **5.18 receipts per transaction**.

### 2d. Reconciling an earlier mismatch (honest note)
Our first exploratory script (2026-11-04) sampled 20 consecutive blocks at 2026-11-04 11:46 UTC: 122 tx in 12.8 s ≈ 9.5 tx/s ≈ 820k/day, which did not match nearblocks' 597,189 for 2026-11-03. Resolved, with data:
1. **Wrong day compared.** The sample was taken on 11-04, whose nearblocks count is 706,690 (8.2 tx/s), not 11-03.
2. **Short windows are noisy.** `scripts/window_noise.py` reads 30 random 20-block windows of 2026-11-08: tx/s ranges p10 **2.73**, median **5.57**, p90 **10.48** (day average 7.05). 9.5 tx/s is a normal 20-block reading; a 13-second window cannot estimate a day.
3. **Off-by-one in the old script.** It divided the tx of 20 blocks by the time of 19 intervals (+5%). Fixed in `window_noise.py`.
4. **Not receipts.** Both nearblocks `txns` and our count are *signed transactions*. Counting receipts would give ~5× more (2c), far from the gap observed.
5. **Missing-chunk double count checked.** NEAR re-carries an old chunk header when a shard misses a block; we count only chunks with `height_included == block height` (2 re-carried headers seen in 1,200 blocks — negligible).
Conclusion: nearblocks' daily `txns` is a correct count of signed transactions; use it for long series and use the random-block sample as an independent audit.

## 3. Why this matters long term
- **Value capture moved.** A chain whose security budget comes from gas needs ever more transactions. NEAR's fee engine today is Intents: 35× the gas fees with 17% of transactions. Growth in cross-chain volume, not in L1 spam, is what feeds NEAR holders (via buybacks).
- **Agent and chain-abstraction demand.** Intents is the settlement path that wallets, agents and cross-chain front-ends integrate (DefiLlama counts fees across all integrators); that demand does not require users to hold NEAR or even know they touched NEAR.
- **Cheap L1 is a feature here.** Low gas (about $5.5k/day) keeps settlement costs low, which is what lets a 15.6 bps take rate be competitive.

## 4. Valuation sanity check (not a price target)
At a $22.6M/yr captured-revenue run-rate, NEAR trades at ~211× captured revenue (0.47% yield). The thesis is therefore **directional**: it needs captured revenue to compound for years. It is not a "cheap today" argument.

## 5. Risks
- **Concentration and competition:** cross-chain swap volume can move to rival intent/solver networks; take rate can compress.
- **Data dependence:** Intents USD figures come from DefiLlama's adapter. We verify the transaction share onchain, not the USD value.
- **Policy risk:** the buyback is a governance decision and can change.
- **Volatility:** monthly volume swings ±50% (2025-11 $3.66B → 2025-12 $2.01B).

## 6. Kill criteria (re-check monthly with `./run_all.sh`)
The thesis is wrong, and should be dropped, if any of these hold for **3 consecutive months**:
1. Intents 30d gross fees fall below the same 30 days a year earlier (`findings.intents.fees_usd.pct_yoy < 0`).
2. NEAR-captured share of fees falls below 15% (`captured_share_of_fees_30d < 0.15`; today 0.321).
3. Intents fees fall below 10× L1 gas fees (`intents_fees_vs_l1_gas_fees_30d_x < 10`; today 34.9).
4. The share of signed transactions sent to `intents.near` falls below 5% (`reconciliation.sample.intents_share_of_tx`; today 0.174).

## 7. Reproduce
`./run_all.sh` (full, ~25–35 min) or `./run_all.sh --quick` (~10–15 min). Exact snapshot day: `DAY=2026-11-08 ./run_all.sh`. Outputs: `data/findings.json`, `docs/REPORT.md`, `docs/index.html`. Sources and endpoints: README.md.

*Research, not financial advice.*
