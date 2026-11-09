#!/usr/bin/env python3
"""Compute every number used in THESIS.md from data/*.csv|json and render:
  data/findings.json   machine-readable numbers (one source of truth)
  docs/REPORT.md       auto-generated table of findings
  docs/index.html      static dashboard (inline SVG, no JS, no CDN)
Usage: python3 scripts/build.py [sample_day=latest data/sample_*.json]"""
import csv, json, glob, os, sys, html, datetime as dt
from collections import defaultdict

C = list(csv.DictReader(open("data/nearblocks_daily.csv")))
I = list(csv.DictReader(open("data/intents_daily.csv")))
num = lambda v: float(v) if v not in ("", None) else 0.0
end = min(C[-1]["date"], I[-1]["date"])            # last day present in both sources
C = [r for r in C if r["date"] <= end]; I = [r for r in I if r["date"] <= end]

def win(rows, k, n, back=0):
    sl = rows[len(rows) - n - back: len(rows) - back]
    return sum(num(r[k]) for r in sl), sl[0]["date"], sl[-1]["date"]
def pct(a, b): return round(100 * (a / b - 1), 1) if b else None

F = {"snapshot_end_utc": end, "built_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
     "sources": {"chain": "https://api.nearblocks.io/v1/charts",
                 "intents": "https://api.llama.fi/summary/dexs/near-intents , https://api.llama.fi/summary/fees/near-intents",
                 "sample": "https://archival-rpc.mainnet.fastnear.com (JSON-RPC block + chunk)"}}

# 1) Base-layer activity (nearblocks)
ch = {}
for k in ("txns", "active_accounts", "new_accounts", "txn_fee"):
    a, d0, d1 = win(C, k, 30); b, _, _ = win(C, k, 30, 30); y, y0, y1 = win(C, k, 30, 365)
    ch[k] = {"avg_30d": round(a / 30, 1), "window": [d0, d1], "prev_30d_avg": round(b / 30, 1), "pct_vs_prev_30d": pct(a, b),
             "same_30d_year_ago_avg": round(y / 30, 1), "year_ago_window": [y0, y1], "pct_yoy": pct(a, y)}
ma = [(C[j]["date"], sum(num(r["txns"]) for r in C[j - 29:j + 1]) / 30) for j in range(29, len(C))]
pk = max(ma, key=lambda x: x[1])
ch["txns_30d_avg_peak"] = {"date": pk[0], "value": round(pk[1])}
gas_usd = sum(num(r["txn_fee"]) * num(r["near_price"]) for r in C[-30:])
ch["gas_fees_usd_30d"] = round(gas_usd)
ch["gas_fees_near_30d"] = round(sum(num(r["txn_fee"]) for r in C[-30:]), 1)
ch["near_price_last"] = num(C[-1]["near_price"])
F["chain"] = ch

# 2) NEAR Intents (DefiLlama)
it = {}
for k in ("volume_usd", "fees_usd", "revenue_usd"):
    a, d0, d1 = win(I, k, 30); b, _, _ = win(I, k, 30, 30); y, y0, y1 = win(I, k, 30, 365)
    it[k] = {"sum_30d": round(a), "window": [d0, d1], "prev_30d": round(b), "pct_vs_prev_30d": pct(a, b),
             "same_30d_year_ago": round(y), "year_ago_window": [y0, y1], "pct_yoy": pct(a, y)}
it["volume_usd_cumulative"] = round(sum(num(r["volume_usd"]) for r in I))
it["first_day"] = I[0]["date"]
it["buyback_usd_since_2026_02_23"] = round(sum(num(r["holders_revenue_usd"]) for r in I if r["date"] >= "2026-02-23"))
it["revenue_run_rate_usd_year"] = round(it["revenue_usd"]["sum_30d"] * 365 / 30)
it["fee_take_rate_bps_30d"] = round(1e4 * it["fees_usd"]["sum_30d"] / it["volume_usd"]["sum_30d"], 2)
it["captured_share_of_fees_30d"] = round(it["revenue_usd"]["sum_30d"] / it["fees_usd"]["sum_30d"], 3)
it["intents_fees_vs_l1_gas_fees_30d_x"] = round(it["fees_usd"]["sum_30d"] / gas_usd, 1)
if os.path.exists("data/nearblocks_stats.json"):
    st = json.load(open("data/nearblocks_stats.json"))
    it["market_cap_usd"] = round(float(st["market_cap"])); it["market_cap_fetched_at_utc"] = st["fetched_at_utc"]
    it["revenue_run_rate_pct_of_market_cap"] = round(100 * it["revenue_run_rate_usd_year"] / it["market_cap_usd"], 2)
F["intents"] = it
monthly = defaultdict(lambda: defaultdict(float))
for r in I:
    for k in ("volume_usd", "fees_usd", "revenue_usd"): monthly[r["date"][:7]][k] += num(r[k])
for r in C:
    monthly[r["date"][:7]]["gas_usd"] += num(r["txn_fee"]) * num(r["near_price"])
    monthly[r["date"][:7]]["txns"] += num(r["txns"])
F["monthly"] = {m: {k: round(v) for k, v in d.items()} for m, d in sorted(monthly.items()) if m >= "2024-01"}

# 3) Reconciliation: independent block sample vs nearblocks count
S = sorted(glob.glob("data/sample_*.json"))
if len(sys.argv) > 1: S = [f"data/sample_{sys.argv[1]}.json"]
if S:
    s = json.load(open(S[-1]))["summary"]; d = s["day_utc"]
    nb = next((r for r in C if r["date"] == d), None)
    rec = {"day_utc": d, "sample": s}
    if nb:
        rec["nearblocks_txns"] = int(num(nb["txns"])); rec["nearblocks_blocks"] = int(num(nb["blocks"]))
        lo, hi = s["tx_per_day_95ci"]; rec["nearblocks_inside_95ci"] = lo <= rec["nearblocks_txns"] <= hi
        rec["diff_pct"] = pct(s["tx_per_day_est"], rec["nearblocks_txns"])
        rec["blocks_diff_pct"] = pct(s["blocks_produced_est"], rec["nearblocks_blocks"])
    wn = f"data/window_noise_{d}.json"
    if os.path.exists(wn): rec["short_window_noise"] = json.load(open(wn))["summary"]
    F["reconciliation"] = rec

os.makedirs("docs", exist_ok=True)
json.dump(F, open("data/findings.json", "w"), indent=1)

# ---------- REPORT.md ----------
def M(x): return f"${x/1e6:,.2f}M"
r, c, i = F.get("reconciliation", {}), F["chain"], F["intents"]
L = [f"# Findings (auto-generated by scripts/build.py, data through {end} UTC)", "",
     "| # | Metric | Value | Source |", "|---|---|---|---|",
     f"| 1 | Tx/day, 30d avg ({c['txns']['window'][0]}..{c['txns']['window'][1]}) | {c['txns']['avg_30d']:,.0f} ({c['txns']['pct_vs_prev_30d']:+}% vs prev 30d, {c['txns']['pct_yoy']:+}% YoY) | nearblocks |",
     f"| 2 | Tx/day 30d avg peak | {c['txns_30d_avg_peak']['value']:,} on {c['txns_30d_avg_peak']['date']} | nearblocks |",
     f"| 3 | Active accounts/day, 30d avg | {c['active_accounts']['avg_30d']:,.0f} ({c['active_accounts']['pct_yoy']:+}% YoY) | nearblocks |",
     f"| 4 | New accounts/day, 30d avg | {c['new_accounts']['avg_30d']:,.0f} ({c['new_accounts']['pct_yoy']:+}% YoY) | nearblocks |",
     f"| 5 | L1 gas fees, last 30d | {c['gas_fees_near_30d']:,.0f} NEAR = {M(c['gas_fees_usd_30d'])} | nearblocks (fee x daily price) |",
     f"| 6 | Intents swap volume, last 30d | {M(i['volume_usd']['sum_30d'])} ({i['volume_usd']['pct_vs_prev_30d']:+}% vs prev 30d, {i['volume_usd']['pct_yoy']:+}% YoY) | DefiLlama |",
     f"| 7 | Intents cumulative volume since {i['first_day']} | {M(i['volume_usd_cumulative'])} | DefiLlama |",
     f"| 8 | Intents gross fees, last 30d | {M(i['fees_usd']['sum_30d'])} ({i['fees_usd']['pct_yoy']:+}% YoY); take rate {i['fee_take_rate_bps_30d']} bps | DefiLlama |",
     f"| 9 | Intents fees / L1 gas fees, last 30d | {i['intents_fees_vs_l1_gas_fees_30d_x']}x | rows 5 and 8 |",
     f"| 10 | NEAR-captured Intents revenue, last 30d | {M(i['revenue_usd']['sum_30d'])} ({i['captured_share_of_fees_30d']*100:.1f}% of fees); run-rate {M(i['revenue_run_rate_usd_year'])}/yr | DefiLlama |",
     f"| 10b | Revenue run-rate / NEAR market cap ({i.get('market_cap_fetched_at_utc','')[:10]}) | {i.get('revenue_run_rate_pct_of_market_cap')}% of {M(i.get('market_cap_usd',0))} | DefiLlama + nearblocks /v1/stats |",
     f"| 11 | Buyback funded by Intents revenue since 2026-02-23 | {M(i['buyback_usd_since_2026_02_23'])} | DefiLlama (holdersRevenue) |"]
if r:
    s = r["sample"]
    L += [f"| 12 | Independent tx/day estimate {r['day_utc']} ({s['heights_sampled']} random blocks) | {s['tx_per_day_est']:,} (95% CI {s['tx_per_day_95ci'][0]:,}..{s['tx_per_day_95ci'][1]:,}) vs nearblocks {r.get('nearblocks_txns', 0):,} -> inside CI: {r.get('nearblocks_inside_95ci')}; receipts ~{s.get('receipts_per_day_est', 0):,}/day ({s.get('receipts_per_tx')} per tx) | archival RPC |",
          f"| 13 | Share of signed tx sent to intents.near ({r['day_utc']}) | {s['intents_share_of_tx']*100:.1f}% (~{s['intents_tx_per_day_est']:,} tx/day) | archival RPC sample |"]
    if "short_window_noise" in r:
        w = r["short_window_noise"]
        L += [f"| 14 | 20-block windows, tx/s spread ({w['windows']} windows) | p10 {w['tx_per_s_p10']} / median {w['tx_per_s_median']} / p90 {w['tx_per_s_p90']} (day avg {r.get('nearblocks_txns',0)/86400:.2f}) | archival RPC |"]
open("docs/REPORT.md", "w").write("\n".join(L) + "\n")

# ---------- index.html (inline SVG) ----------
def svg_line(points, title, ylab, w=760, h=240, color="#2b6cb0", logy=False):
    import math
    xs = list(range(len(points))); ys = [p[1] for p in points]
    f = (lambda v: math.log10(max(v, 1))) if logy else (lambda v: v)
    lo, hi = min(map(f, ys)), max(map(f, ys)); hi = hi if hi > lo else lo + 1
    X = lambda k: 50 + (w - 70) * k / max(1, len(xs) - 1); Y = lambda v: h - 30 - (h - 60) * (f(v) - lo) / (hi - lo)
    path = " ".join(f"{'M' if k == 0 else 'L'}{X(k):.1f},{Y(v):.1f}" for k, v in enumerate(ys))
    ticks = "".join(f'<text x="{X(k):.0f}" y="{h-10}" font-size="10" text-anchor="middle">{points[k][0]}</text>'
                    for k in range(0, len(points), max(1, len(points) // 8)))
    yl = f'<text x="50" y="14" font-size="11">{html.escape(ylab)} (max {max(ys):,.0f}, last {ys[-1]:,.0f})</text>'
    return (f'<figure><figcaption>{html.escape(title)}</figcaption><svg viewBox="0 0 {w} {h}" width="100%" role="img">'
            f'<rect width="{w}" height="{h}" fill="#fff"/>{yl}<path d="{path}" fill="none" stroke="{color}" stroke-width="1.6"/>{ticks}</svg></figure>')
txma = [(d, v) for d, v in ma if d >= "2023-01-01"][::7]
mon = [(m, d) for m, d in F["monthly"].items() if m >= "2024-12"]
charts = [svg_line(txma, "NEAR signed transactions per day, 30-day average (nearblocks)", "tx/day"),
          svg_line([(m, d.get("volume_usd", 0)) for m, d in mon], "NEAR Intents swap volume per month, USD (DefiLlama)", "USD/month", color="#2f855a"),
          svg_line([(m, d.get("fees_usd", 0)) for m, d in mon], "NEAR Intents gross fees per month, USD (DefiLlama)", "USD/month", color="#c05621"),
          svg_line([(m, d.get("gas_usd", 0)) for m, d in mon], "NEAR L1 gas fees per month, USD (nearblocks fee x price)", "USD/month", color="#6b46c1")]
rows = "".join("<tr>" + "".join(f"<td>{html.escape(x.strip())}</td>" for x in l.strip("|").split("|")) + "</tr>" for l in L[4:])
open("docs/index.html", "w").write(f"""<!doctype html><meta charset="utf-8"><title>Semilla1 NEAR Thesis - dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font:14px system-ui,sans-serif;max-width:820px;margin:24px auto;padding:0 12px;color:#222}}td{{border-top:1px solid #ddd;padding:4px;vertical-align:top}}figure{{margin:18px 0}}figcaption{{font-weight:600}}</style>
<h1>Semilla1 NEAR Thesis: from transactions to Intents fees</h1>
<p>Static, re-runnable dashboard. Data through <b>{end} UTC</b>, built {F['built_at_utc']}. Every number comes from <code>data/findings.json</code>,
produced by <code>./run_all.sh</code> from public, keyless sources. Thesis text: <a href="https://github.com/semilla1lab/semilla1-near-thesis/blob/main/THESIS.md">THESIS.md</a>.</p>
<table><tr><th>#</th><th>Metric</th><th>Value</th><th>Source</th></tr>{rows}</table>
{''.join(charts)}
<p>Sources: {html.escape(F['sources']['chain'])}; {html.escape(F['sources']['intents'])}; {html.escape(F['sources']['sample'])}.</p>
""")
print(open("docs/REPORT.md").read())
