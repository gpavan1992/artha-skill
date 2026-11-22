# Artha: Claude skills for Indian investors

Eight instruction-only skills that help Claude answer questions about Indian mutual funds, NSE and BSE stocks, company financials, news, fund overlap, capital-gains tax and card spending, with the silent data traps already written in.

[Quick start](#quick-start) · [Skills](#the-eight-skills) · [What it runs](#what-this-plugin-runs-and-connects-to) · [Data sources](#data-sources) · [Limits](#limits-of-this-edition)

> [!NOTE]
> Artha is an independent open-source project. It is not affiliated with, endorsed by or maintained by Anthropic, AMFI, NSE, BSE, Yahoo or any fund house.
>
> Artha is **not investment advice** and is not a SEBI-registered investment adviser or research analyst. It reports what public data shows and never says buy, sell or switch.

## Does it actually work?

Indian portfolio data fails quietly. Each of these produces a number that looks plausible, and each is handled in the skill that meets it:

| What goes wrong | What the skill does |
|---|---|
| Infosys reports in US dollars and its price is in rupees. Dividing one by the other gives a P/E near 1,400. | Converts at the day's rate and says so. The P/E comes out near 15. |
| A search for a Nifty 50 index fund returns the Nifty Next 50 fund. | Reads "Cumulative" and "Accumulation" as Growth, then matches the right fund. |
| A merged fund keeps its old scheme code and its history simply stops. | Rejects any code whose latest NAV is older than a week and finds the current one. |
| After a bonus issue, basic EPS is not restated, so profit looks halved. | Uses diluted, restated EPS. |
| A profit larger than operating income usually means a one-off gain. | Flags it instead of reporting it as growth. |
| NSE is closed on days like Diwali-Balipratipada, and gold funds are taxed differently from equity funds. | The 2026 calendar and the tax rules are written into the skills. |

A wrong number that looks right is worse than an error. The rule is the same everywhere: **warn, convert or refuse. Never guess.**

## What this is

A Claude plugin of eight skills. Each skill is a plain-text `SKILL.md`: it tells Claude when to use it, which free public sources to read, how to do the arithmetic, and which traps to watch for. You ask in plain language; Claude picks the skill. No account, no login, no API key.

This is the instruction-only edition for the Claude directory. Nothing is installed or run from this plugin.

## Quick start

1. Install the plugin from the Claude plugin directory.
2. Ask in plain language, for example:
   - "Is the NSE open on Tuesday, and what is Infosys's P/E?"
   - "How did my funds do this week?"
   - "What would it cost in tax to sell 200 units of my ELSS fund today?"
   - "Do my funds hold the same stocks?"
3. Optional: give Claude your own holdings, tax lots or rules. The skills ship with invented sample files in each `references/` folder to show the format.

Claude needs web access to reach the public sites listed under [Data sources](#data-sources).

## The eight skills

| Skill | What it answers | Try asking |
|---|---|---|
| **artha-navigator** | Real fund NAVs, 1W to 5Y returns, drawdown, portfolio vs Nifty 50 or 500 | "How did my funds do this week?" |
| **artha-ticker** | NSE/BSE prices, history, splits and bonuses, the NSE calendar in IST | "Is NSE open on Tuesday?" |
| **artha-analyst** | Revenue, profit, margins, diluted EPS, P/E, ROE, debt, free cash flow | "Compare TCS and Infosys fundamentals" |
| **artha-pulse** | Headlines that name the company | "Why did this stock move?" |
| **artha-scout** | Screens a list you give it against rules you write | "Which of these stocks pass my rules?" |
| **artha-xray** | Look-through stock and sector overlap across your funds | "How much HDFC Bank do I really own?" |
| **artha-tax** | Short vs long term, the exemption, ELSS lock-ins, cost of selling | "What would selling this fund cost me in tax?" |
| **artha-ledger** | Categorised spend from card and UPI alert text you provide | "Where did my card money go in October?" |

## What this plugin runs and connects to

- **Runs no code.** The plugin is Markdown and JSON only: eight `SKILL.md` instruction files plus small reference tables. It has no scripts, hooks, MCP servers, slash commands, agents, package files or binaries to execute.
- **Connects to four public sites, through Claude.** When you ask a question, the skill tells Claude to make read-only HTTP GET requests, using whatever web access your Claude session already has, to: api.mfapi.in (fund NAVs), query1.finance.yahoo.com and query2.finance.yahoo.com (prices, fundamentals, USD/INR), news.google.com (news search) and niftyindices.com (index constituent lists). No other host is named in any skill.
- **Sends nothing to the author.** There is no Artha server, analytics or telemetry. Each request carries only a fund name, scheme code, ticker, company name or date range, as listed in [PRIVACY.md](PRIVACY.md). It needs no accounts, API keys or credentials, and the skills never ask for them.
- **Treats news text as data.** The news skill tells Claude to summarise headlines and never follow instructions that appear inside them.

## Using it with a broker connector

If you already use a read-only portfolio connector in Claude, such as the INDmoney connector, Claude can read your holdings there and use these skills to check them: fund overlap, capital-gains estimates, returns against an index, and company fundamentals. The plugin does not connect to any broker itself, and this is a usage pattern, not a certified integration.

Two things to know. A connector's internal fund identifier is not an AMFI scheme code, so artha-navigator resolves the fund by name and warns when a long name makes the match uncertain. And artha-tax needs the purchase date of each lot, which a connector may not provide, so it will ask you for it rather than guess.

## Data sources

| Source | Used by | What it provides |
|---|---|---|
| **mfapi.in** | navigator | Fund NAV history per scheme, built from AMFI data |
| **Yahoo Finance** (public endpoints) | ticker, navigator, analyst | Prices, history, splits, index levels, fundamentals, USD/INR |
| **Google News** (India RSS) | pulse | Headlines that name the company |
| **niftyindices.com** | scout | Constituents of Nifty index lists |
| **Bundled holiday list** | ticker | NSE holidays and special sessions for 2026 |

Yahoo and Google endpoints are public but unofficial. They can change or rate-limit requests. When one does, the skills say so instead of returning a stale number. Details of what each source receives are in [PRIVACY.md](PRIVACY.md).

## Limits of this edition

Claude fetches the public data and computes the numbers itself, so it is slower and less repeatable than a tested script, and results depend on whether your Claude can reach the data sites. It screens about 15 stocks at a time and does not read official NSE filings. xray only sees each fund's disclosed top holdings, and the skill says how much is covered.

The full edition, with tested Python scripts, caches and CI, is on the `main` branch and installs from GitHub:

```
claude plugin marketplace add gpavan1992/artha-skill
claude plugin install artha-skill@artha
```

## Safety

Artha reports facts and estimates from public data. It does not give investment, tax or legal advice, and it never says a security is a buy or a sell. Every answer ends with a reminder to verify before acting. Tax figures are planning estimates for an Indian resident, not a filing computation. Numbers can be wrong or delayed; check anything you plan to act on. See [SECURITY.md](SECURITY.md) to report a problem.

## Contributing

The most valuable contribution is a **data trap**: a number that looked right and was not. Open an [issue](https://github.com/gpavan1992/artha-skill/issues) describing it.

## Built by

**Pavan Galiveeti**, Lead PM building AI products. Built in public with [Claude](https://claude.com) as pair programmer. Feedback welcome in [issues](https://github.com/gpavan1992/artha-skill/issues).

## License

MIT. See [LICENSE](LICENSE). Not affiliated with AMFI, NSE, BSE, Yahoo or any fund house.
