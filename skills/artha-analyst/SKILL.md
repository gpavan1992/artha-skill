---
name: artha-analyst
description: Reported financials for NSE/BSE-listed Indian companies — annual and quarterly revenue, net profit, operating margin, growth, diluted EPS, P/E, ROE, debt-to-equity and free cash flow, with traps (bonus/split EPS, one-off profits, bank metrics) flagged. Use whenever the user asks how an Indian company is doing financially, "is Reliance profitable", "compare TCS and Infosys fundamentals", "what's Infosys's P/E", earnings growth, or needs numbers behind a stock idea — even if they only name the company.
---

# India Fundamentals

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/fund.py" INFY RELIANCE HDFCBANK [--json] [--out fundamentals.json]
```

Bare symbols default to NSE (`.NS`). Find symbols with artha-ticker (`prices.py resolve`).
Source: Yahoo Finance's public fundamentals time series (no key). NSE and BSE block
automated access, so this is the reliable free route. Figures are in **₹ crore**; EPS is in ₹.
Cached for 12 hours in `./.fund-cache`.

## Output per company

`annual[]` (last 4 FYs: revenue, net income, operating margin), `revenue/profit_growth_yoy_pct`,
`net_margin_pct`, `roe_pct`, `debt_to_equity`, `free_cash_flow_cr`, `quarters[]` (latest 4,
YoY where the year-ago quarter exists), `eps_ttm` with its basis, `pe`, `splits_bonuses`,
`reporting_currency`, and `warnings[]`.

## Traps this tool handles — always pass warnings through

1. **Bonus issues and splits.** Basic EPS isn't restated: HDFC Bank's basic EPS "halved"
   after its 1:1 bonus while profit grew. The tool uses **diluted (restated) EPS** and lists
   split/bonus dates.
2. **One-off profits.** When net profit exceeds operating income (exceptional gains,
   debt-restructuring write-backs, deferred-tax credits), the year is flagged.
   Don't call it business growth.
3. **Banks and NBFCs.** No operating income; their "debt" is deposits. D/E and operating
   margin are suppressed. Yahoo's bank figures can be consolidated: verify ROE and profit
   against the bank's own results before relying on them.
4. **TTM EPS.** It's the sum of 4 quarters when all are available, otherwise the last
   full-year EPS (stated in `eps_basis`). Loss-making companies get no P/E.
5. **Fiscal years** end in March; `fy_end` "2026-03" = FY2025-26.
6. **Reporting currency.** Yahoo reports some companies' financials in another currency
   (Infosys in US dollars) while the share price is in ₹. Dividing one by the other gave a P/E
   of ~1,450. Every series is now converted to ₹ at today's rate and the conversion is
   disclosed in `warnings` and `reporting_currency`. Absolute ₹ amounts and P/E are then
   approximate; growth, margins and ROE are unaffected. If the rate can't be fetched, the
   figures are dropped, never mixed. Always pass this warning through.

## How to report

Lead with the 2–3 numbers that answer the question (e.g. "revenue +54%, profit +53%,
P/E ~24"), then the caveats from warnings. Compare against the sector's valuation from
web search when judging "expensive or cheap". Facts only: no buy/sell calls or targets.
