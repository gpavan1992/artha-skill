# Changelog

Format: [Keep a Changelog](https://keepachangelog.com). Versions follow [SemVer](https://semver.org).

## [0.2.0] - 2026-11-14

### Changed
- Directory edition (branch `directory`): all eight skills rewritten as instruction-only. Claude fetches the public data and computes the results itself. The Python scripts, shell tests and GitHub workflows are not part of this edition, because the Claude directory accepts only text, Markdown, JSON, YAML and images from unverified publishers.
- Fund resolution uses mfapi.in search plus a freshness check instead of the AMFI file.
- Returns use small date-window requests instead of the full NAV history.
- `artha-scout` screens about 15 stocks per run. `artha-pulse` no longer reads NSE announcements.
- Reference data (NSE 2026 holidays, tax rules with a worked example, spend categories, example inputs) moved into each skill's `references/` folder.

### Unchanged
- The tested script edition continues on `main` (v0.1.x) and installs from GitHub.
