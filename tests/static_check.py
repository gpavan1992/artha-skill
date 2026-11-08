#!/usr/bin/env python3
"""Offline checks: manifests, SKILL.md frontmatter, example JSON, script syntax. No network."""
import json, re, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
errors = []


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                      # noqa: BLE001
        errors.append(f"{p.relative_to(root)}: invalid JSON ({e})")


plugin = load(root / ".claude-plugin" / "plugin.json") or {}
market = load(root / ".claude-plugin" / "marketplace.json") or {}
if not plugin.get("version"):
    errors.append("plugin.json: version missing")
if not market.get("description"):
    errors.append("marketplace.json: description missing")
names = [p.get("name") for p in market.get("plugins", [])]
if plugin.get("name") not in names:
    errors.append("marketplace.json does not list the plugin named in plugin.json")

skills = sorted(p for p in (root / "skills").iterdir() if p.is_dir())
if not skills:
    errors.append("no skills found")
for d in skills:
    md = d / "SKILL.md"
    if not md.exists():
        errors.append(f"{d.name}: SKILL.md missing")
        continue
    m = re.match(r"---\nname:\s*(\S+)\ndescription:\s*(.+?)\n---", md.read_text(encoding="utf-8"), re.S)
    if not m:
        errors.append(f"{d.name}: SKILL.md frontmatter missing or malformed")
    else:
        if m.group(1) != d.name:
            errors.append(f"{d.name}: frontmatter name '{m.group(1)}' must equal the folder name")
        if len(m.group(2)) < 60:
            errors.append(f"{d.name}: description too short to trigger reliably")
    for j in d.rglob("*.json"):
        load(j)
    for py in d.glob("scripts/*.py"):
        try:
            compile(py.read_text(encoding="utf-8"), str(py), "exec")   # syntax check; writes nothing
        except SyntaxError as e:
            errors.append(f"{py.relative_to(root)}: {e}")

if errors:
    print("FAILED:\n  " + "\n  ".join(errors))
    sys.exit(1)
print(f"ok: {len(skills)} skills, manifests valid, scripts compile")
