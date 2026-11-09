#!/usr/bin/env bash
# Re-run the whole thesis from public, keyless sources. Needs only bash + python3 (stdlib) + internet.
#   ./run_all.sh            full run (1200-block sample of yesterday UTC, ~25-35 min on public RPC)
#   ./run_all.sh --quick    quick check (200-block sample, ~10-15 min; wider confidence interval)
#   DAY=2026-11-08 ./run_all.sh   re-check a specific UTC day (the one used in THESIS.md)
set -euo pipefail; cd "$(dirname "$0")"
DAY="${DAY:-$(date -u -d yesterday +%F)}"; N=1200; [ "${1:-}" = "--quick" ] && N=200
python3 scripts/fetch_daily.py
python3 scripts/fetch_intents.py
python3 scripts/sample_day.py "$DAY" "$N" 42
python3 scripts/window_noise.py "$DAY" 30 20 7
python3 scripts/build.py "$DAY"
echo "Done: data/findings.json, docs/REPORT.md, docs/index.html"
