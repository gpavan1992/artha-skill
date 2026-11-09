# Privacy

Artha runs on your machine. Its developer (Pavan Galiveeti) runs no server, receives no data from Artha, and collects nothing: no analytics, no telemetry, no accounts, no logs.

*Last updated: 2026-11-09 (version 0.1.3)*

## What stays on your machine

- **Your personal files:** holdings, tax lots, fund holdings, screening rules and bank-alert exports. Artha reads only the files you name on the command line. It never uploads them.
- **The skills that handle your personal data make no network requests at all.** `artha-tax` (tax lots), `artha-xray` (fund holdings) and `artha-ledger` (bank alerts) contain no network code.
- **Caches of public data** (NAVs, prices, financials, headlines), in `.mfnav-cache`, `.prices-cache`, `.fund-cache` and `.news-cache` folders next to where you run the scripts, or in the folders set by the environment variables listed in the README. They hold public data only. Delete them whenever you like.
- **Files you ask for:** output files you request with `--out` and "already seen" lists you request with `--state`.

## What is sent to other services

Five skills fetch public data. Each request contains only what is needed to look something up: a ticker symbol, a mutual-fund scheme code, a company name or an index name. Requests never contain your holdings, amounts, tax lots, bank data or any personal detail. Those services see your IP address and Artha's User-Agent, as any website does.

| Service | Used by | What is sent |
|---|---|---|
| AMFI (`portal.amfiindia.com`) | navigator | Nothing specific: the full scheme list is downloaded and matched on your machine |
| mfapi.in | navigator | A mutual-fund scheme code |
| Yahoo Finance (`query1`, `query2`) | ticker, navigator, analyst, pulse | A ticker or index symbol, a currency pair, or a company name for lookup |
| Google News (`news.google.com`) | pulse | A company name in a news search |
| NSE index lists (`www.niftyindices.com`, `nsearchives.nseindia.com`) | scout | An index name, to pick the constituent list to download |
| NSE announcements (`www.nseindia.com`) | pulse, **only with `--nse`** | A ticker symbol. Off by default. NSE refuses clients that identify themselves, so this one call sends a browser-style User-Agent and a cookie handshake |

Every other request sends the User-Agent `artha-skill/0.1.3 (+https://github.com/gpavan1992/artha-skill)`.

## Retention

Artha keeps nothing except the caches and files described above, all on your machine. Cache entries are reused for 20 minutes to 24 hours and then refreshed. Delete the cache folders to remove them. Artha's developer retains no data because none reaches the developer.

## Third parties

The services above run their own systems and have their own privacy policies and logs. Artha does not control them. Check their terms before relying on or redistributing their data.

## Claude

Artha is a plugin for Claude. What you ask and what the scripts return are handled by Claude under Anthropic's own privacy policy. Artha does not read Claude's memory or chat history, and it does not store conversation content.

## Age

Artha is a tool for analysing investments and is not intended for people under 18.

## Questions

Open an issue at https://github.com/gpavan1992/artha-skill/issues. For security problems, see [SECURITY.md](SECURITY.md).
