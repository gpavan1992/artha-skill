---
name: artha-scout
description: Screens NSE stocks (Nifty 50/100/200/500, Next 50, Midcap 150, Smallcap 100, or any list) against the user's own rules on reported fundamentals — growth, profit, P/E, ROE, debt, one-off profits — and returns passes, near-misses (failing one rule, with the gap) and failures with reasons. Use when the user asks to "screen", "filter", "find stocks that…", "which Nifty stocks have…", wants Indian stock ideas backed by numbers, or wants to check whether their holdings still meet their criteria.
---

# India Screener

Needs the **artha-analyst** skill installed alongside it. The screener imports its
`fund.py` from the sibling folder, or from the path in `FUND_PY`.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/screen.py" --index nifty100 [--rules my_rules.json] [--out screen.json] [--json]
python3 "${CLAUDE_SKILL_DIR}/scripts/screen.py" --symbols INFY RELIANCE ITC
python3 "${CLAUDE_SKILL_DIR}/scripts/screen.py" --metrics fundamentals.json      # reuse fund.py --out
```

Indices: `nifty50, niftynext50, nifty100, nifty200, nifty500, midcap150, smallcap100`
(official NSE constituent lists, with industry). Speed: ~40 s per 50 stocks the first time,
cached for 12 hours after that.

## Rules (`rules.example.json`)

```json
{"name": "...", "rules": [{"field": "pe", "op": "<=", "value": 35, "label": "P/E ≤ 35"}]}
```

Ops: `>= <= > < == !=`. Fields come from artha-analyst: `kind` ("company" or
"bank/financial"), `revenue_growth_yoy_pct`, `profit_growth_yoy_pct`, `net_margin_pct`,
`roe_pct`, `debt_to_equity`, `pe`, `eps_ttm`, `one_off_latest`,
`latest_quarter_revenue_yoy_pct`.

**The rules are the user's.** If they haven't given any, show the example rules and ask what
to change before screening. Don't silently impose your own thresholds.

## How it decides

- **Missing data always fails.** A missing number never passes.
- **Passers are ranked by headroom:** the average margin by which they clear numeric
  thresholds. It's an ordering, not a rating.
- **Near misses** fail exactly one rule, and the gap is shown. Often the most useful list.
- The example rules exclude **banks/financials** (`kind == company`) because D/E and
  operating margin don't apply to them. Screen banks with their own rules
  (e.g. ROE, profit growth).
- Each result carries artha-analyst' warnings (one-offs, bonus EPS, bank data caveats).
  Mention any that apply to a passer.

## How to report

"N of 50 pass: <names>." Then the near misses and what they missed by, then
caveats. A pass means "meets your rules on reported numbers", never "buy". Suggest
artha-pulse for any passer the user wants to dig into.
