---
name: artha-ticker
description: NSE/BSE stock and ETF prices, history, splits/bonuses and the NSE trading calendar (IST hours, holidays, Muhurat sessions), from free public data. Use whenever the user asks about an Indian stock's price, 52-week range, how their Indian stocks did this week or vs Nifty, price history, "is the market open today/tomorrow", NSE holidays, or when a dashboard or digest needs Friday-to-Friday moves for NSE/BSE holdings — even if they just name a company (e.g. "how's Reliance doing"). For Indian mutual fund NAVs use artha-navigator instead.
---

# India Prices

Prices for NSE/BSE stocks, ETFs and indices, plus the NSE calendar, so weekly numbers line
up with real trading days.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/prices.py" --help
```

Standard library Python, no keys. Prices are Yahoo Finance data, **delayed ~15 minutes**.
Responses are cached in `./.prices-cache` (20 minutes for prices, 1 day for searches).

## Commands

```bash
prices.py resolve "Reliance"               # company/ETF name → RELIANCE.NS / RELIANCE.BO
prices.py quote INFY RELIANCE nifty500     # price, day change, 52-week range, % from high
prices.py history RELIANCE --range 1y --interval 1wk [--out file.json]   # OHLC + splits/dividends
prices.py weekly stocks.json --weeks 12 --benchmark nifty500 [--out weekly.json]
prices.py market [--date 2026-11-10T11:00]  # open/closed now (IST), reason, next trading day
```

- Bare symbols default to NSE (`INFY` → `INFY.NS`); add `.BO` for BSE.
- Benchmarks: `nifty50`, `nifty500`, `banknifty`, or any Yahoo index symbol (`^NSEI`).
- `stocks.json` (see `stocks.example.json`): `{"stocks": [{"symbol": "INFY", "value": 7500}]}`.
  Each entry takes `value` (today's ₹, converted to units at the latest close) or `units`.
- `weekly --out` writes `dates, value, wow, idx, bwow, bidx, summary {ret, bret, beat_weeks},
  stocks, warnings`, the same shape as artha-navigator's portfolio output, so the two can be
  combined into one total.

## Traps this tool handles

1. **Holiday Fridays.** If NSE was shut on a Friday (e.g. 2 Oct 2026), the weekly series uses
   that week's last trading close and says so in `warnings`.
2. **Splits and bonuses.** Raw prices halve on a 1:1 bonus. `quote` and `weekly` detect splits
   inside the window and use adjusted closes. Never compare raw prices across a split.
3. **Yahoo's exchange codes flip** (NSI/NSE, BSE/BOM). Resolution relies on the `.NS`/`.BO`
   suffix instead.
4. **Mutual fund rows in search.** Hidden: they aren't reliable NAVs. Use artha-navigator.
5. **Stale symbols.** If the last price is more than 5 days old, `quote` flags it (suspended,
   delisted or wrong symbol). Don't present it as current.
6. **Calendar gaps.** `data/nse_holidays.json` holds NSE's published list (2026 loaded).
   When a year is missing, `market` says so and assumes weekends only. When NSE publishes the
   next year's list (usually in December), web-search it, cross-check two sources, and add it
   in the same format, including special sessions like Muhurat trading.

## How to report

- Lead with the answer (price, move or market status), then context such as the
  benchmark gap or % from the 52-week high.
- Always give the as-of time in IST and say prices are delayed.
- Pass warnings through: holidays used, splits, stale symbols.
- Past prices only. No buy/sell calls, targets or predictions.
