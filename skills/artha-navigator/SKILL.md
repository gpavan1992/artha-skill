---
name: artha-navigator
description: Real NAV history, returns and weekly performance for Indian mutual funds, from AMFI and mfapi.in (free, no keys). Use whenever the user asks how an Indian mutual fund or their MF portfolio performed — weekly or monthly returns, 1Y/3Y/5Y CAGR, drawdown, "how did my funds do this week", "compare my fund with Nifty 500", "find the AMFI scheme code", "NAV history", or when a dashboard or digest needs real (not estimated) MF numbers. Also use to resolve fund names to the correct, current AMFI scheme code before any other MF analysis, even if the user doesn't mention AMFI.
---

# India MF NAV

IND Money, CAS statements and most apps show a fund's value today, not its path. This skill
gets the real daily NAV for any Indian mutual fund and turns it into returns, weekly series
and a portfolio-vs-benchmark comparison.

Tool (standard library Python, no keys, caches in `./.mfnav-cache` for 12 hours):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/nav.py" --help
```

## Sources

| What | Source |
|---|---|
| Active schemes, codes, ISINs, today's NAV | AMFI `NAVAll.txt` (official, daily) |
| Full daily NAV history | `api.mfapi.in/mf/<code>` |
| Benchmarks: `nifty50`, `nifty500`, `banknifty` (or any Yahoo symbol, e.g. `^NSEI`) | Yahoo Finance chart API |

## Commands

```bash
# 1. Resolve names to the CURRENT scheme code (always do this first)
nav.py resolve "UTI Nifty 50 Index"                       # Direct · Growth by default
nav.py resolve "Parag Parikh Flexi Cap" --plan regular
nav.py resolve --isin INF879O01027                   # exact, preferred when you have it

# 2. Returns: 1W (Friday→Friday), 1M, 3M, 6M, 1Y, 3Y/5Y CAGR, 1Y max drawdown
nav.py returns 120716 122639 --benchmark nifty500 [--json]

# 3. Portfolio: weekly value-weighted series vs a benchmark
nav.py portfolio holdings.json --weeks 12 --benchmark nifty500 [--out weekly.json] [--json]
```

`holdings.json` (see `holdings.example.json`): `{"as_of": "YYYY-MM-DD", "funds": [{"name": ..., "value": ...}]}`.
Each fund may instead carry `code`, `isin` or `units`. `value` must be as of `as_of`: the tool
divides it by the NAV on that date to get units.

`--out` writes: `dates`, `value`, `wow`, `idx`, and with a benchmark `bwow`, `bidx`,
`summary {ret, bret, beat_weeks}`, plus `funds` (codes used) and `warnings`. These field
names match a weekly dashboard's `vs_market.mf` block.

## Traps this tool handles — and you must not undo

1. **Stale codes.** Merged or renamed funds keep their old code with history that just stops
   (one popular fund's old code ends in 2018). Always resolve via AMFI, which lists only active
   schemes. The tool flags any history older than 7 days as stale. Never use a stale series.
2. **"Growth" has aliases.** ICICI calls it *Cumulative*; others say *Accumulation*. The
   resolver treats them as Growth. Without this, it silently picks a different fund
   (e.g. Nifty **Next** 50 instead of Nifty 50).
3. **Blank plan/option.** AMFI leaves Plan and Option empty for some schemes (e.g. some international fund-of-funds): Direct and Regular look identical. The tool picks the higher NAV for
   Direct (lower costs → higher NAV) and warns. Ask for the ISIN to be sure.
4. **FoF naming.** "FoF" and "Fund of Fund(s)" are normalised to the same token.
5. **Weak matches.** Below 0.5 there is no match. Any match under 1.00 produces a
   "check match" warning: show it to the user. Never present a guessed fund as certain.

## How to report

- Lead with the number that answers the question, then the comparison
  ("12 weeks: your funds −1.1% vs Nifty 500 −0.6%; beat it in 6 of 12 weeks").
- Always state the as-of date and that units are held constant (new SIP money is excluded
  from the portfolio series).
- Pass every warning through. Unresolved or stale funds are listed, not hidden.
- Past returns only. Never say a fund is a buy or sell, or predict returns.

## Safety

Education and tooling, not financial advice. The skill only reads public NAV data.
