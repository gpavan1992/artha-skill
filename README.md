# Artha: Claude skills for Indian investors

Artha is a set of eight skills that help Claude answer questions about Indian mutual funds, NSE and BSE stocks, company financials, news, fund overlap, capital-gains tax and card spending. Each skill is a plain-text instruction file: it tells Claude which free public sources to read, how to do the arithmetic, and which silent data traps to avoid. Nothing is installed or run from this plugin.

## What the skills do

| Skill | Ask Claude things like |
|---|---|
| artha-navigator | "How did my funds do this week?", "1-year return of Parag Parikh Flexi Cap", "find the scheme code" |
| artha-ticker | "How's Reliance doing?", "Is NSE open on Tuesday?", "My stocks vs Nifty 500 this week" |
| artha-analyst | "What's Infosys's P/E?", "Is Reliance profitable?", "Compare TCS and Infosys fundamentals" |
| artha-pulse | "Why did this stock move?", "Any news on HDFC Bank?" |
| artha-scout | "Which of these stocks pass my rules?", "Screen the Nifty 50 names I list for growth under 35 P/E" |
| artha-xray | "Do my funds hold the same stocks?", "How much HDFC Bank do I really own?" |
| artha-tax | "What would selling this fund cost me in tax?", "When do my ELSS units unlock?" |
| artha-ledger | "Where did my card money go in October?" |

## The data traps these instructions encode

- A merged fund keeps its old scheme code and its history simply stops. The skill rejects any code whose latest NAV is older than a week.
- "Cumulative" and "Accumulation" mean Growth. Without that, a search for a Nifty 50 index fund returns the Nifty Next 50 fund.
- Infosys reports in US dollars while its price is in rupees. Dividing one by the other gives a P/E near 1,400; converted, it is about 15.
- Basic EPS is not restated after bonus issues, so a profitable bank can look like its earnings halved. The skills use diluted EPS.
- A profit larger than operating income usually means a one-off gain, not growth.
- NSE closes on days like Diwali-Balipratipada, and equity gains are taxed differently from gold-fund gains. The calendar and tax rules are written into the skills.

## Limits of this edition

This is the instruction-only edition for the Claude directory. Claude fetches the public data and computes the numbers itself, so it is slower and less repeatable than a tested script, and results depend on whether your Claude can reach the data sites. It screens about 15 stocks at a time and does not read official NSE filings. The full edition, with tested Python scripts, caches and CI, is on the `main` branch and installs from GitHub:

```
claude plugin marketplace add gpavan1992/artha-skill
claude plugin install artha-skill@artha
```

## Data sources

mfapi.in (fund NAVs), Yahoo Finance (prices, index levels, fundamentals, USD/INR), Google News India (headlines), and the official Nifty index constituent lists from niftyindices.com. Details of what each receives are in [PRIVACY.md](PRIVACY.md).

## Safety

Artha reports facts and estimates from public data. It does not give investment, tax or legal advice, and it never says a security is a buy or a sell. Every answer ends with a reminder to verify before acting. Tax figures are planning estimates for an Indian resident, not a filing computation. Numbers can be wrong or delayed; check anything you plan to act on. See [SECURITY.md](SECURITY.md) to report a problem.

## License

MIT. See [LICENSE](LICENSE). Not affiliated with AMFI, NSE, BSE, Yahoo or any fund house.
