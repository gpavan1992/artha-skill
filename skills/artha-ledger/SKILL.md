---
name: artha-ledger
description: Turns Indian bank and credit-card transaction alert emails (HDFC, ICICI, SBI Card, Axis, Kotak, Amex and others) into a categorised spending summary — categories, top merchants, per-card totals, refunds — without storing card numbers, UPI IDs or names of people paid. Use when the user asks where their money went, wants monthly spend analysis, spending patterns, "how much did I spend on Swiggy/fuel/Amazon", or a spend section for a budget or dashboard — even if they just say "analyse my card spends".
---

# Card Spend Parser

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/parse.py" alerts.json [--period "October 2026"] [--cards-only] [--include-transfers] [--out spend.json] [--json]
```

## Getting alerts (Gmail)

1. `search_threads`: `(credit card) (spent OR debited OR "used for") after:YYYY/MM/01 before:YYYY/MM/01 -subject:statement`,
   pageSize 50, following `nextPageToken`.
2. Threads showing exactly 5 messages may hold more: call `get_thread`.
3. If the snippet cuts off before the merchant (SBI Card does this), call `get_message`
   with PLAIN_TEXT and use the body.
4. Write `alerts.json` = `[{"id", "date": "YYYY-MM-DD", "subject", "text"}]`.

**Never open statement PDFs or try their passwords.** Alerts are enough.

## Output (`--out`)

`period, total, txns, categories[], cards[], top_merchants[] (top 8), refunds,
transfers_excluded, coverage, unparsed[]`. This matches a dashboard's `spend` block; add
`patterns[]` yourself in plain language (frequency, time-of-day habits, one-off big days).

## Rules built in

- **Skipped:** OTPs, statements, payment-received and credit messages, declines.
- **Refunds and reversals** are netted off the total.
- **Duplicates** (same amount, date and card) are counted once. Banks often send two alerts.
- **Privacy:** UPI IDs and names of people paid are never output. Account → UPI-ID debits
  become "UPI/transfer to a person" and are excluded from spend unless
  `--include-transfers` is passed. Cards show only their last 4 digits.
- **Categories** come from `categories.json` (keyword → category). Edit it, don't hard-code.
  Anything unmatched goes to "Other". If "Other" exceeds 15%, add keywords and rerun.

## Report

Lead with the total and the top 2 categories, then 2–4 patterns ("11 quick-commerce orders, mostly in the morning"). Always state coverage ("63 of 69 alerts parsed"). Don't moralise about
spending.
