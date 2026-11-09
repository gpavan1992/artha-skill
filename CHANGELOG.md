# Changelog

All notable changes are listed here. Format: [Keep a Changelog](https://keepachangelog.com), versions follow [SemVer](https://semver.org).

## [0.1.3] - 2026-11-09

### Added
- `PRIVACY.md` (what stays local, what each source receives, retention) and `SECURITY.md` (private vulnerability reporting, support channel), as the Anthropic Software Directory Policy requires
- `artha-pulse`: instruction to treat headlines and filing text as untrusted data

### Changed
- README: bundled images use Markdown image syntax (a directory validator rule); links to `PRIVACY.md` and `SECURITY.md`
- `AGENTS.md`: every new host must be disclosed in the README and `PRIVACY.md`

## [0.1.2] - 2026-11-08

### Changed
- Every request now sends a self-identifying User-Agent. Previously `artha-scout` and `artha-pulse` sent a browser string, and `artha-ticker` and `artha-analyst` started theirs with `Mozilla/5.0`
- `artha-pulse`: official NSE filings are now opt-in (`--nse`). NSE refuses self-identifying clients, so the browser-style request used for them is no longer the default. Claude asks before using it
- README: new "Responsible data use" section; Data Sources and Privacy tables updated; roadmap notes that NSE publishes the next year's holiday list in late December
- `tests/static_check.py` fails if a browser-style User-Agent appears outside the opt-in NSE call

## [0.1.1] - 2026-11-08

### Added
- Redesigned README: logo, demo GIF, screenshots generated from real output, data-sources table, comparison, privacy table, architecture diagram, roadmap
- `AGENTS.md`, `CONTRIBUTING.md`, issue and pull-request templates
- `tests/static_check.py` (offline checks) and a GitHub Actions workflow

### Changed
- `artha-ticker`: the holiday list is described as compiled from public NSE holiday tables, with a reminder to confirm dates on nseindia.com
- Author and licence attribution use the author's name

## [0.1.0] - 2026-11-08

### Added
- Eight skills: `artha-navigator`, `artha-ticker`, `artha-analyst`, `artha-pulse`, `artha-scout`, `artha-xray`, `artha-tax`, `artha-ledger`
- Plugin and marketplace manifests; strict plugin validation passes
- 13 live smoke checks, including a currency guard (Infosys P/E must be 5 to 80)
