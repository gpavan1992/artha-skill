---
name: artha-tax
description: Indian capital-gains estimates for mutual funds, shares, gold/silver funds, debt funds and foreign shares/RSUs — short vs long term, tax if sold, ₹1.25L LTCG exemption harvesting, ELSS lock-in dates and "what would selling X cost me". Use whenever an Indian resident asks about tax on redeeming or switching a fund, selling shares or RSUs, tax-loss or tax-gain harvesting, when units become long-term, or when ELSS units unlock — even if they only ask "can I sell this" or "what's the tax hit".
---

# India Tax

Planning estimates for an Indian resident's capital gains under FY 2026-27 rules. It is not a
filing computation: always say "estimate" and suggest the IND Money/CAMS capital-gains
report or a CA for filing.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/tax.py" --help
```

## Rules encoded (verified Nov 2026: Budget 2026 left rates unchanged)

| type | Long-term after | LT rate | ST rate |
|---|---|---|---|
| `equity` (equity MF, index fund, equity FoF) | >12 months | 12.5% above ₹1.25L/FY | 20% |
| `elss` | >12 months, **plus a 3-year lock-in per lot** | same | same |
| `listed_share` (NSE/BSE shares, equity ETFs) | >12 months | 12.5% above ₹1.25L/FY | 20% |
| `other_listed` (gold/silver/international ETFs) | >12 months | 12.5%, no exemption | slab |
| `other_unlisted` (gold/silver/international FoFs) | >24 months | 12.5%, no exemption | slab |
| `foreign_share` (US/Canadian shares, vested RSUs) | >24 months | 12.5% | slab |
| `specified_debt` (>65% debt) | bought before 1 Apr 2023: >24 months; on/after: **never** | 12.5% | slab |

The ₹1.25L exemption is **one per financial year**, shared across all equity LTCG (funds and
shares). The tool adds 4% cess. Surcharge is not included; say so if income is very high.
Equity bought before 1 Feb 2018 can carry `fmv_2018` for grandfathering.

Re-verify these rules after each Union Budget (web-search "capital gains tax rates
<FY> mutual funds"), and update `RULES` and `EXEMPTION_112A` if they change.

## Input: lots.json

See `lots.example.json`. Each lot has `asset, type, buy_date, units`, either `cost` (total)
or `buy_price`, and `current_price`, which you can instead supply via `--prices prices.json`
from artha-navigator / artha-ticker. Optional: `realized_ltcg_this_fy`. Lot dates come from
IND Money's capital-gains or transaction report, or the CAS. For SIPs, every instalment
is its own lot.

## Commands

```bash
tax.py gains   lots.json [--slab 30] [--realized 40000]    # every lot: ST/LT, gain, unlock/LT dates, tax if all sold
tax.py whatif  lots.json --sell "Sample ELSS Fund:220"   # FIFO redemption: which lots go, tax, lock-in blocks
tax.py harvest lots.json [--realized 40000]                  # units to redeem to use the ₹1.25L exemption tax-free
tax.py lockin  lots.json                                     # ELSS lots and unlock dates
```

## Traps this tool handles

1. **FIFO.** Redemptions take the oldest units first per folio, and you can't choose lots.
   `whatif` and `harvest` follow FIFO, and `harvest` stops before any short-term or locked lot.
2. **ELSS lock-in is per instalment.** A 2021 SIP lot can be free while a 2024 lot in the
   same fund is locked. `whatif` blocks locked units.
3. **Gold/silver FoFs are not equity.** They need 24 months, get no ₹1.25L exemption, and are
   taxed at slab rate before that.
4. **Debt funds bought on or after 1 Apr 2023 are always slab-rate.**
5. **Foreign shares and RSUs need 24 months.** RSU cost basis = market value on the vest date.
6. **Switching = selling.** A switch between funds is a taxable redemption.

## How to report

Lead with the tax number and what drives it ("~₹1,900, mostly the US shares being
short-term"), then any locks and dates. Never advise whether to sell. Show what each choice
costs and when it gets cheaper ("the US shares become long-term on 11 Mar 2028").
