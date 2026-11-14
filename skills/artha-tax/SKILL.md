---
name: artha-tax
description: Indian capital-gains estimates for mutual funds, shares, gold/silver funds, debt funds and foreign shares or RSUs: short vs long term, tax if sold, the Rs 1.25 lakh LTCG exemption, ELSS lock-in dates and "what would selling X cost me". Use when an Indian resident asks about tax on redeeming or switching a fund, selling shares or RSUs, tax-loss or tax-gain harvesting, when units become long-term, or when ELSS units unlock.
---

# Artha Tax: capital-gains estimates (FY 2026-27)

Instruction-only skill. This is a planning estimate, not a filing computation. Always say "estimate" and point to the capital-gains report from the fund house, CAMS/KFintech or the broker, or a chartered accountant, for filing. You do the arithmetic yourself (code execution if you have it, otherwise show the working).

## Rules

Read `references/tax-rules.md` for the table, the exemption, FIFO, lock-in, and a worked example you can use to check your method. Re-verify the rates by web search after each Union Budget; if what you find differs, tell the user and use the newer rule.

## Input

Ask for lots (one row per purchase; each SIP instalment is its own lot): asset, type, buy date, units, total cost (or buy price), current price. Dates come from the capital-gains or transaction report or the CAS. Current prices come from artha-navigator (funds) or artha-ticker (shares). Also ask for long-term gains already realised this financial year, and the user's slab rate if short-term gains on non-equity assets matter. Equity bought before 1 Feb 2018 needs its 31 Jan 2018 value for grandfathering; ask for it.

## What to produce

- **gains**: for every lot, short or long term, gain, the date it turns long term, and ELSS unlock date; then total tax if all sold.
- **what-if** ("what if I sell 220 units of X"): redeem **FIFO**, oldest units first within a folio. The user cannot pick lots. Block ELSS units still in lock-in. Show which lots go, the gain, and the tax.
- **harvest**: units to redeem to use the remaining ₹1.25 lakh exemption tax-free. Stop before any short-term or locked lot.
- **lock-in**: ELSS lots and their unlock dates.

## How to report

Lead with the tax number and what drives it ("about ₹1,900, mostly the US shares being short-term"), then any locks and dates. Never advise whether to sell: show what each choice costs and when it gets cheaper ("the US shares become long-term on 11 Mar 2028"). Mention that surcharge is not included, which matters at high incomes.

Footer on every answer: *AI-generated estimate. Not tax advice. Verify with a chartered accountant before you act.*
