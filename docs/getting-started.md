# Getting started (ContextBridge v0.1.0)

This guide walks through one **demo** handoff using the sample technical-proposal package.

For product overview see the [root README](../README.md). For host discovery see [host-matrix.md](host-matrix.md). For document index see [README.md](README.md) in this folder.

## Prerequisites

- This repository cloned and opened in an Agent Skills–capable host (Cursor is the primary verified host).
- Ability to run Agent chats that can read files under `skills/` and `examples/`.
- For the optional Validator helper: **Python 3** + [`requirements-validator.txt`](../requirements-validator.txt).

You do **not** need a cloud dashboard or database.

## Enable the three Skills (out of box)

Canonical Skill bodies (source of truth):

```text
skills/context-exporter/SKILL.md
skills/context-validator/SKILL.md
skills/context-importer/SKILL.md
```

### A) Always works — path-invoke

In Agent chat, name the skill and point at its `SKILL.md` (and linked `references/`). No install required.

### B) Auto-discovery — install mirrors (recommended)

From the **repository root**:

```bash
python scripts/install_skills.py
# Windows: pwsh scripts/install-skills.ps1
# Unix:    bash scripts/install-skills.sh
```

This creates directory links (does **not** copy files) under:

| Path | Typical hosts |
| --- | --- |
| `.agents/skills/<name>/` | Cursor, Codex, OpenCode, … |
| `.claude/skills/<name>/` | Claude Code |
| `.cursor/skills/<name>/` | Cursor project skills |

Then verify:

```bash
pip install -r requirements-validator.txt
python scripts/doctor.py
```

Doctor exit code `0` means canonical skills, discovery links, schemas, deps, and sample Validator smoke all look good. See [host-matrix.md](host-matrix.md) for what is `verified` vs `unverified` per host.

## Demo materials

| Path | Role |
| --- | --- |
| [`examples/technical-proposal/input/`](../examples/technical-proposal/input/) | Synthetic source docs. May contain **fake** secret strings for redaction drills — not real credentials. |
| [`examples/technical-proposal/generated-output/`](../examples/technical-proposal/generated-output/) | Ready-made CBHF 0.1.0 package for Validator + Importer demos. |
| [`examples/technical-proposal/expected-output/EXPECTED.md`](../examples/technical-proposal/expected-output/EXPECTED.md) | Human notes for the sample. |

## 1) Exporter (optional for the sample)

The sample already includes `generated-output/`. To practice export on your own docs:

1. Ask the Agent to follow [`skills/context-exporter/SKILL.md`](../skills/context-exporter/SKILL.md) (or the discovered skill name `context-exporter`).
2. Provide readable source paths and an **empty** output directory for a new package root.
3. Confirm the Exporter-required tree appears (see README package layout).
4. Exporter must **not** create a fake `validation/` folder (CBHF 0.1.0: session reports only; in-package `validation/` write is reserved and not enabled).

## 2) Validator

Ask the Agent to follow [`skills/context-validator/SKILL.md`](../skills/context-validator/SKILL.md).

Preferred deterministic helper (from **repository root**):

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
```

Optional local schemas (default is already repo `spec/cbhf/v0.1.0`):

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output --schema-dir spec/cbhf/v0.1.0
```

Behavior (from the script):

- Prints a **session JSON** report to stdout (CBHF 0.1.0 authority).
- Does **not** write into the package — `validation/` is reserved but **write not enabled**.
- Exit code `1` only if `final_status` is `invalid`; otherwise `0` (including warnings / `not_fully_validated` / `semantically_unreviewed`).

Save stdout if you will feed it to Importer (for example redirect to a file **outside** the package — do not invent `validation/` inside the package).

Interpret layers honestly:

- L1–L3 `PASS` ≠ semantic adequacy.
- L4 / `H01`–`H06` remaining `NOT_CHECKED` is expected when L4 was not performed.
- No **session** report ⇒ not validated yet (missing packaged `validation/` is expected in 0.1.0).

## 3) Importer

Ask the receiving Agent to follow [`skills/context-importer/SKILL.md`](../skills/context-importer/SKILL.md).

Typical prompts:

- **Normal:** import `examples/technical-proposal/generated-output` and attach the Validator session JSON if you have one.
- **Unvalidated:** same package **without** a Validator report → expect `structurally_unvalidated_in_this_session`.
- **Invalid package:** use a failing tree only with clear force intent → expect block or `UNTRUSTED_STRUCTURE`.

The Agent should emit a **Receiver Understanding Report** in the **chat session** (12 sections). It must **not** write that report into the CBHF package.

How to read the report:

1. Package identity + validation gate banner.
2. Facts bucketed by KnowledgeStatus (watch `inferred` / `disputed`).
3. Unknowns labeled **OPEN — DO NOT FILL**.
4. Conflicts with both stances; no auto winner.
5. Limitations: L4 unfinished, redaction best-effort, read-only import.

## 4) What “done” looks like for this demo

- You can open `generated-output/manifest.yaml` and see `cbhf_version: "0.1.0"`.
- Validator JSON shows L1–L3 results without claiming L4 PASS.
- Importer report preserves ids such as `unk_001` and `cfl_001` without inventing answers.
- Package files are unchanged after Validator/Importer (read-only skills/scripts).
- `python scripts/doctor.py` exits 0 after install + pip deps.

## Next reading

- Host matrix: [`host-matrix.md`](host-matrix.md)
- Protocol (human): [`skills/context-exporter/references/cbhf-format.md`](../skills/context-exporter/references/cbhf-format.md)
- Schemas: [`spec/cbhf/v0.1.0/`](../spec/cbhf/v0.1.0/)
- E2E notes: [`tests/validator/e2e/README.md`](../tests/validator/e2e/README.md), [`tests/importer/e2e/README.md`](../tests/importer/e2e/README.md)
