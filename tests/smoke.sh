#!/usr/bin/env bash
# Network smoke test: runs one safe command per skill. Exit code 0 = all passed.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; S="$ROOT/skills"; W="$(mktemp -d)"; cd "$W"
fail=0
run() { name="$1"; shift; if "$@" >/dev/null 2>"$W/err"; then echo "ok    $name"; else echo "FAIL  $name"; head -3 "$W/err"; fail=1; fi; }
run navigator-resolve  python3 "$S/artha-navigator/scripts/nav.py" resolve "UTI Nifty 50 Index"
run navigator-portfolio python3 "$S/artha-navigator/scripts/nav.py" portfolio "$S/artha-navigator/holdings.example.json" --weeks 4 --benchmark nifty500
run ticker-quote       python3 "$S/artha-ticker/scripts/prices.py" quote RELIANCE INFY
run ticker-market      python3 "$S/artha-ticker/scripts/prices.py" market
run ticker-weekly      python3 "$S/artha-ticker/scripts/prices.py" weekly "$S/artha-ticker/stocks.example.json" --weeks 4 --benchmark nifty500
run analyst            python3 "$S/artha-analyst/scripts/fund.py" INFY
if python3 "$S/artha-analyst/scripts/fund.py" INFY --json 2>/dev/null | python3 -c "import json,sys; o=json.load(sys.stdin)[0]; assert o['pe'] and 5 < o['pe'] < 80, o['pe']"; then echo "ok    analyst-currency (INFY P/E is sane)"; else echo "FAIL  analyst-currency (INFY P/E out of range: USD/INR mix-up?)"; fail=1; fi
run pulse              python3 "$S/artha-pulse/scripts/news.py" INFY --days 7
run scout              python3 "$S/artha-scout/scripts/screen.py" --symbols INFY RELIANCE ITC
run xray               python3 "$S/artha-xray/scripts/overlap.py" "$S/artha-xray/example.indmoney.json" --values "$S/artha-xray/example.values.json"
run tax-gains          python3 "$S/artha-tax/scripts/tax.py" gains "$S/artha-tax/lots.example.json" --slab 30
run tax-harvest        python3 "$S/artha-tax/scripts/tax.py" harvest "$S/artha-tax/lots.example.json"
run ledger             python3 "$S/artha-ledger/scripts/parse.py" "$S/artha-ledger/alerts.example.json"
rm -rf "$W"; exit $fail
