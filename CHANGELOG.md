# Changelog

All notable changes are listed here. Format: [Keep a Changelog](https://keepachangelog.com), versions follow [SemVer](https://semver.org).

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
