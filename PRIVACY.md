# Privacy

Artha is a set of text instructions for Claude. Its developer (Pavan Galiveeti) runs no server, receives no data from Artha, and collects nothing: no analytics, no telemetry, no accounts, no logs.

*Last updated: 2026-11-14 (version 0.2.0)*

## What Artha stores

Nothing. Artha contains no code and no storage. It does not read Claude's memory or chat history.

## Your personal data

Holdings, tax lots, fund holdings, screening rules and bank-alert text are used only inside your conversation with Claude, which handles them under Anthropic's own privacy policy. The instructions tell Claude not to put personal details (card numbers, UPI IDs, names of people paid) into any web request or into its output.

## Public data Claude may fetch

When you ask a question, Claude may read public websites to answer it. A request contains only what is needed for the lookup: a ticker symbol, a mutual-fund scheme code or name, a company name, an index name or a currency pair. It never contains your holdings, amounts, tax lots or bank data. These services see your IP address or Claude's, as any website does.

| Service | Used by | What is sent |
|---|---|---|
| mfapi.in | navigator | A fund name for search, a scheme code and a date range |
| Yahoo Finance | ticker, navigator, analyst | A ticker or index symbol, a currency pair, or a company name for lookup |
| Google News (news.google.com) | pulse | A company name in a news search |
| niftyindices.com | scout | An index name, to read its constituent list |

## Third parties

Those services run their own systems and have their own privacy policies. Artha does not control them. Check their terms before relying on or redistributing their data.

## Age

Artha is a tool for analysing investments and is not intended for people under 18.

## Questions

Open an issue at https://github.com/gpavan1992/artha-skill/issues. For security problems, see [SECURITY.md](SECURITY.md).
