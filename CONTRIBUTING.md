# Contributing to Artha

Thanks for helping. The most valuable contribution is a **data trap**: a number that looked right and was not.

## Report a problem

- **A wrong or stale number:** open an issue with the *Data source broke* template. Include the command, the output, and what you expected.
- **A bug in a script:** use the *Bug report* template.
- **A tax rule that is out of date:** open a pull request that cites the source (Income Tax Act section, budget notification, or CBDT circular).

## Set up

Fork the repository on GitHub and clone your fork. Then, from its folder:

```bash
python3 tests/static_check.py
bash tests/smoke.sh        # needs network
```

Python 3.9+. No packages to install.

## Pull requests

1. Fork, then branch from `main`.
2. Keep changes small and focused: one skill or one rule per PR.
3. Run `python3 tests/static_check.py` and, if you touched a script, `bash tests/smoke.sh`.
4. Use invented data in examples. Never include your real holdings.
5. Describe what changed and why, and paste the before/after output for any number that changed.

Read [AGENTS.md](AGENTS.md) for the hard rules (standard library only, no advice, warn-convert-refuse).

## Conduct

Be kind and specific. Assume good faith. Critique code and data, not people.

## License

By contributing you agree that your contribution is licensed under the MIT License.
