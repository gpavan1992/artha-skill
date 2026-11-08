# Artha

Skills for Indian investors, for Claude. They cover the things a mixed portfolio of Indian
mutual funds and stocks needs and most tools skip: real fund NAV history, NSE/BSE prices and
the market calendar, company financials, news and filings, a rules-based screener, fund
overlap, capital-gains estimates and spend parsing.

> **Not investment advice.** Artha reports data and applies rules you set. It never says buy or
> sell. See [Disclaimer](#disclaimer).

## The skills

| Skill | What it does | Data |
|---|---|---|
| `artha-navigator` | Real mutual fund NAV history, weekly returns and portfolio-vs-benchmark | AMFI, mfapi.in, Yahoo Finance (indices) |
| `artha-ticker` | NSE/BSE prices, history, splits and the NSE market calendar | Yahoo Finance; bundled NSE holiday list |
| `artha-analyst` | Company financials: revenue, profit, margins, EPS, P/E, ROE, debt | Yahoo Finance fundamentals |
| `artha-pulse` | What happened to a company: NSE filings and news that names it | NSE announcements, Google News |
| `artha-scout` | Screen Nifty indices against your own rules, with near-misses | NSE index lists + artha-analyst |
| `artha-xray` | Look through your funds: shared stocks, sector and concentration | Fund holdings you supply (e.g. from a broker/app) |
| `artha-tax` | Capital-gains estimates, ELSS lock-ins, LTCG harvesting (FY2026-27 rules) | Rules encoded in the script; you supply lots |
| `artha-ledger` | Bank/card alert emails to categorised spend, privacy-safe | Alert emails you supply |

Each skill is a folder in `skills/` with a `SKILL.md` (instructions for Claude) and a
standard-library Python script. No API keys, no dependencies beyond Python 3.9+.

## Install

Claude Code:

```bash
claude plugin marketplace add gpavan1992/artha-skill
claude plugin install artha-skill@artha
```

Then ask in plain language: *"How did my funds do against the Nifty 500 this week?"*,
*"Is the market open on Tuesday?"*, *"What would selling these units cost me in tax?"*

Try it locally first: `claude --plugin-dir ./artha-skill`.

## Network access

The scripts fetch public data from your machine or sandbox, so outbound web access is needed to:
`query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `api.mfapi.in`, `portal.amfiindia.com`,
`news.google.com`, `www.nseindia.com`, `nsearchives.nseindia.com`, `www.niftyindices.com`.

## Where the numbers come from, and how far to trust them

- **Fund NAVs:** AMFI's daily file and mfapi.in. Resolution maps names to *active* scheme codes
  and flags stale histories, because merged funds keep dead codes.
- **Prices and fundamentals:** Yahoo Finance's public endpoints. Prices are delayed (~15 min).
  These endpoints are unofficial and can change or fail. The tools say so when they do.
- **News and filings:** NSE corporate announcements (official, sometimes blocked to scripts) and
  Google News headlines that name the company.
- **Tax:** rules for FY2026-27 are encoded in `skills/artha-tax/scripts/tax.py`. They are an
  estimate for planning, not a computation for filing.
- **Holdings and lots:** you supply them (files or pasted data). Nothing is read from your
  accounts.

## Keeping it current

- NSE holidays: add each new year to `skills/artha-ticker/data/nse_holidays.json` once NSE
  publishes it (usually December). The tool warns when the next year is missing.
- Tax rules: re-check `RULES` and `EXEMPTION_112A` in `artha-tax` after every Union Budget.
- Smoke test: `bash tests/smoke.sh` (needs network).

## Privacy

Everything runs in your session. The scripts call only the public endpoints above, collect no
telemetry, and never ask for credentials. Holdings files stay where you put them. The example
files contain invented data.

## Disclaimer

Artha is a personal-tooling project. It is not a SEBI-registered investment adviser or research
analyst and does not provide investment, tax or legal advice. Outputs may be wrong, delayed or
unavailable. Past returns do not predict future returns. A screener result means only that
reported numbers met the rules you chose. Verify anything important with the primary source and
a qualified professional before acting.

## Contributing

Issues and pull requests are welcome, especially: corrections to tax rules, new categories for
the spend parser, additional NSE index lists and fixes when a data source changes shape.

## License

MIT. See [LICENSE](LICENSE).
