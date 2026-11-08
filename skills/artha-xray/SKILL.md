---
name: artha-xray
description: Finds stock and sector overlap across an Indian mutual fund portfolio — which funds hold the same stocks, how many rupees you really have in each stock and sector through all funds combined, and which fund pairs largely duplicate each other. Use when the user asks about fund overlap, "do my funds hold the same stocks", diversification, consolidating funds, concentration in banks or any sector, or how much HDFC Bank/ICICI they really own — even if they only say "am I over-diversified" or "too many funds".
---

# India MF Overlap

Look-through analysis of a mutual fund portfolio from each fund's disclosed holdings.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/overlap.py" funds.json [--values values.json] [--top 15] [--flag 30] [--out overlap.json] [--json]
```

## Getting the data

1. **Holdings:** call IND Money `get_mf_funds_details(fund_ids="...", includes=["holdings"])`
   (max 10 ids per call). Save the raw response as JSON. The script reads it directly and
   keeps only the **Equity** group.
2. **Values:** `values.json` = `{"Sample Focused Fund": 250000, ...}`, keyed by the fund's
   short name as IND Money returns it, or by fund_id. Take values from `networth_holdings(MF)`.
3. Or pass your own `funds.json`:
   `[{"name", "value", "holdings": [{"name", "perc", "sector"}]}]`.

## Output

- **pairs:** overlap % for every fund pair (Σ of the smaller weight across common stocks),
  the common stocks, and a flag at ≥30% (`--flag`).
- **top_stocks:** rupees and % of portfolio held in each stock through all funds, and in how
  many funds.
- **sectors:** look-through sector split, also as a share of the visible holdings.
- **coverage_pct** and per-fund warnings: how much of the portfolio the disclosed holdings
  actually explain.

## Traps this tool handles

1. **Partial disclosures.** IND Money usually returns top holdings only; on a real test they
   covered 29–64% of each fund. Every overlap number is therefore a **floor**. Always report
   coverage next to it ("at least 13.6%, from holdings covering 35–64% of each fund").
2. **Bonds named like companies.** Hybrid and debt funds list corporate bonds
   ("Samvardhana Motherson…") under Debt & Cash. Only the Equity group counts as stock overlap.
3. **Name variants.** "Max Healthcare Institute Ltd Ordinary Shares" and "Max Healthcare
   Institute Ltd" are matched after stripping Ltd/Limited/Ordinary Shares/etc.
4. **Index funds** hold the whole index; their overlap with active large-cap funds is
   structural, not a fund-manager choice. Say so instead of flagging it as duplication.

## How to report

Lead with the most useful number: the biggest look-through stock, or the most-duplicated
pair. Then coverage, then what it means for diversification. Observations only; never
tell the user to sell or switch.
