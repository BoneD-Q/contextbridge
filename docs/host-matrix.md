# Host compatibility matrix (CBHF / Skills 0.1.0)

Canonical skills: [`skills/`](../skills/). Discovery mirrors: run [`scripts/install_skills.py`](../scripts/install_skills.py).

Statuses:

| Status | Meaning |
| --- | --- |
| `verified` | Exercised in this repo with the check listed |
| `unverified` | Expected to work via Agent Skills conventions; not claimed until checked |
| `n/a` | Not applicable |

## Matrix

| Host | Auto-discovery after `install_skills.py` | Path-invoke `skills/*/SKILL.md` | Validator Python helper | Notes |
| --- | --- | --- | --- | --- |
| **Cursor** (Agent) | `verified` — `.agents/skills` + `.cursor/skills` | `verified` | `verified` — `scripts/doctor.py` | Primary development host; use `--dest` to link Skills into another project; Exporter fast-path + `scaffold_package.py` reduce stall |
| **Codex** | `unverified` — prefers `.agents/skills` | `unverified` | `verified` (host-agnostic CLI) | Install then open repo root |
| **Claude Code** | `unverified` — prefers `.claude/skills` | `unverified` | `verified` (host-agnostic CLI) | Install creates `.claude/skills` links |
| **OpenCode** | `unverified` — often scans `.agents/skills` | `unverified` | `verified` (host-agnostic CLI) | Same install |
| Any host with file read | `n/a` | `verified` pattern | `verified` if Python deps present | Always can `@` / read `SKILL.md` |

## Out-of-box checklist (any host)

1. Clone repository.
2. `python scripts/install_skills.py` (optional: `--dest /other/project` for cross-repo discovery).
3. `pip install -r requirements-validator.txt`
4. `python scripts/doctor.py` → exit 0 (WARN for missing discovery is OK only before step 2).
5. Ask the agent to follow `context-exporter` / `context-validator` / `context-importer` (or path-invoke the `SKILL.md` files). For export, prefer scaffold + ≤3 docs (see `skills/context-exporter/references/fast-path.md`).
6. Validator smoke (also done by doctor):

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
```

## What we do **not** claim

- Identical agent behavior or tool permissions across hosts.
- Packaged Cursor/Claude marketplace plugins (optional future).
- In-package `validation/` writes (0.1.0 session reports only).

When you verify another host end-to-end, update this table from `unverified` → `verified` and note the date/environment in a PR.
