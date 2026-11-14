---
name: artha-scout
description: Screens NSE stocks against the user's own rules on reported fundamentals (growth, profit, P/E, ROE, debt, one-off profits) and returns passes, near-misses (failing one rule, with the gap) and failures with reasons. Use when the user asks to "screen", "filter", "find stocks that...", "which Nifty stocks have...", or to check whether their holdings still meet their criteria.
---

# Artha Scout: rules-based screener

Instruction-only skill. It uses the **artha-analyst** method for every number, so read that skill's rules first (currency conversion, diluted EPS, one-offs, banks).

## Scope

Fetch data for **at most about 15 stocks per run**; each one needs several calls. For a bigger universe, ask the user to narrow it (a sector, a watchlist, the top names of an index) and say what was left out. Never screen a long list from memory.

## Universe

Official constituent lists (CSV with company, industry, symbol, ISIN): `https://www.niftyindices.com/IndexConstituent/<file>.csv` where file is `ind_nifty50list`, `ind_niftynext50list`, `ind_nifty100list`, `ind_nifty200list`, `ind_nifty500list`, `ind_niftymidcap150list` or `ind_niftysmallcap100list`. Or use the symbols the user gives.

## The rules are the user's

If they have not given rules, show `references/rules.example.json`, ask what to change, then screen. Do not silently impose your own thresholds. A rule is `{field, op, value, label}` with ops `>= <= > < == !=`. Fields: `kind` ("company" or "bank/financial"), `revenue_growth_yoy_pct`, `profit_growth_yoy_pct`, `net_margin_pct`, `roe_pct`, `debt_to_equity`, `pe`, `eps_ttm`, `one_off_latest`, `latest_quarter_revenue_yoy_pct`, each computed as in artha-analyst.

## How to decide

- **Missing data fails.** A missing number never passes.
- **Passes** meet every rule. Order them by headroom (average margin by which they clear numeric thresholds); that is an ordering, not a rating.
- **Near misses** fail exactly one rule: show which and by how much. Often the most useful list.
- The example rules exclude banks and financials because debt-to-equity and operating margin do not apply. Screen banks with their own rules (ROE, profit growth).
- Attach artha-analyst's caveats (one-off profit, bonus EPS, currency conversion, bank data) to any passer they apply to.

## How to report

"N of M pass: <names>", then near misses with their gaps, then caveats. A pass means "meets your rules on reported numbers", never "buy". Suggest artha-pulse for any passer the user wants to look into.

Footer on every answer: *AI-generated from public data. Not investment advice. Verify before you act.*
