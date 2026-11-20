# Host discovery mirrors

Canonical Skill bodies live in [`../../skills/`](../../skills/).

After clone, create discovery links for Cursor / Codex / Claude Code / OpenCode:

```bash
python scripts/install_skills.py
# or: pwsh scripts/install-skills.ps1
# or: bash scripts/install-skills.sh
```

This directory will then contain `context-exporter`, `context-validator`, and `context-importer` links. Do **not** edit linked trees as a second source of truth.
