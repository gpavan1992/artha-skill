# AGENTS.md

Instructions for AI coding agents (and humans) working in this repository.

## What this is

Artha is a Claude Code plugin: eight skills for Indian investors. Each skill is a folder under `skills/` with a `SKILL.md` (when to use it, known traps, how to report) and a standard-library Python script in `scripts/` that fetches and computes the numbers.

## Layout

```
.claude-plugin/        plugin.json + marketplace.json
skills/<artha-name>/   SKILL.md, scripts/, *.example.json
PRIVACY.md, SECURITY.md  what leaves the machine; how to report problems
tests/smoke.sh         live checks against public data (needs network)
tests/static_check.py  offline checks: manifests, SKILL.md frontmatter, script syntax
```

README images (logo, demo GIF, screenshots) live in the screenshots folder and are generated from real output on sample data.

## Commands

```bash
python3 tests/static_check.py     # offline, run before every commit
bash tests/smoke.sh               # live, needs network; run before a release
claude plugin validate --strict . # manifests and skills, needs Claude Code
```

## Hard rules

1. **Standard library only.** No third-party Python packages, no API keys, no logins.
2. **No personal data, ever.** Examples use invented names and amounts. Never commit real holdings, folio numbers, PANs, card numbers, UPI IDs or email addresses.
3. **Never give advice.** Output states what data shows. Do not write "buy", "sell", "switch" or "recommend" in skill output or in `SKILL.md` instructions to Claude.
4. **Warn, convert or refuse. Never guess.** If a number is stale, converted, approximate or missing, say so in the output. Do not fill gaps from memory.
5. **`name` in `SKILL.md` frontmatter must equal the folder name**, and the description must say when to use the skill.
6. **Tax rules carry their source.** If you change a rate, threshold or holding period, cite the source in the pull request and update the table in the README and in `artha-tax/SKILL.md`.
7. **Public endpoints are unofficial.** Handle failures explicitly, keep caches short, and send the self-identifying User-Agent on every request. The only exception is the opt-in NSE filings call in `artha-pulse` (`--nse`): NSE refuses self-identifying clients, so it stays off by default, and `tests/static_check.py` fails if a browser-style User-Agent appears anywhere else.

8. **Disclose every host.** A new data source or a new kind of request must be added to the Data Sources table in the README and to `PRIVACY.md` in the same pull request, with what is sent to it.

## Adding or changing a skill

1. Write or edit `skills/<name>/SKILL.md` and `scripts/`.
2. Add an invented-data example file if the skill takes input.
3. Add a check to `tests/smoke.sh`.
4. Run `python3 tests/static_check.py` and `bash tests/smoke.sh`.
5. Add a line to `CHANGELOG.md`; bump `version` in `.claude-plugin/plugin.json` for any user-visible change (users only receive updates when the version changes).

## Style

Plain, short sentences. Rupee amounts with `₹`. Dates ISO (`2026-11-06`) in tool output. No emojis in script output.
