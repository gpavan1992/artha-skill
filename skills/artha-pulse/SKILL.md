---
name: artha-pulse
description: What happened to an NSE-listed company — official NSE corporate announcements (results, dividends, orders, management changes, credit ratings, regulatory matters) plus Indian news headlines that actually name the company, ranked by importance. Use whenever the user asks why an Indian stock moved, "any news on Reliance", "what did Infosys announce", results or dividend dates, or when a weekly digest needs a "what's new" section for Indian holdings — even if they just name the company.
---

# India News

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/news.py" INFY RELIANCE --days 7 [--state seen.json] [--no-broker-calls] [--max-per-symbol 6] [--out news.json] [--json]
```

NSE symbols (find them with artha-ticker `resolve`). Standard library only, no keys.
Cached for 1 hour in `./.news-cache`.

## Sources, in priority order

1. **NSE corporate announcements:** official filings with a link to the original PDF.
   Marked 🏛 / `official: true`. NSE sometimes blocks automated requests; when it does, the
   tool says so in `notes` and continues with headlines only. Never present headlines as
   official filings.
2. **Google News (India edition):** kept only if the headline names the company. Price-ticker
   pages ("share price live"), market wraps and "stocks to watch" lists are dropped.

## How items are ranked

results & dividends → orders/deals, regulatory, fundraising → management, credit rating →
broker views → other. **Routine investor-meet filings** (schedules, outcomes, transcripts)
are collapsed into a count, because a single company can file 18 of them in two weeks.
Each symbol keeps room for at least 2 headlines alongside official filings.

`--state seen.json` makes repeat runs show only new items (good for weekly jobs).

## How to report

- For each company, lead with what explains the price move: results and their direction,
  the dividend and record date, any order or regulatory event. Then headline context.
- Open and read an article before summarising its claim. Never summarise from the headline
  alone when the user asks *why*. Skip paywalled ones.
- Broker targets are opinions: label them "broker view", never as facts or advice.
- Give dates. Say "no company-specific news" rather than padding with market news.
