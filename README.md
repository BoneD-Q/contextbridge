# ContextBridge

**Skills-first AI-to-AI document handoff** using a shared folder package format (**CBHF 0.1.0**).

ContextBridge is an open-source **Agent Skills** project — not a SaaS product, web dashboard, or standalone application runtime. It helps one AI agent hand work to another **without silently dropping evidence, decisions, unknowns, or conflicts**.

[中文说明](README.zh-CN.md) · [Getting started](docs/getting-started.md) · [Docs index](docs/README.md)

## The problem

When one AI produces documents for another AI (or for a later session), critical context is often lost:

- What was treated as a **fact** vs an **inference**
- Which claims are backed by **locatable evidence**
- Which **decisions** were confirmed, and how
- What remains **unknown**
- Where sources **conflict** and must not be auto-resolved

Plain Markdown dumps and chat summaries usually collapse these distinctions.

## Design ideas

1. **CBHF Package is the handoff carrier** — a versioned folder with manifest, sources, knowledge, evidence, uncertainty, and handoff files.
2. **Skills-first** — agents follow `SKILL.md` instructions; Python exists only as an optional Validator helper.
3. **Honest epistemology** — KnowledgeStatus values (`verified`, `user_confirmed`, `inferred`, `unverified`, `unknown`, `disputed`) are preserved; Importer must not upgrade them.
4. **Structure ≠ semantics** — automated L1–L3 checks are not L4 human semantic review.
5. **Gaps stay gaps** — Unknowns are not web-filled; Conflicts are not auto-adjudicated.
6. **Missing validation ≠ passed** — no Validator **session** report (and no packaged `validation/`, which 0.1.0 does not write) means “not validated yet”.

## Three Skills

| Skill | Role |
| --- | --- |
| [`context-exporter`](skills/context-exporter/SKILL.md) | Read user documents (host-capable), build a CBHF 0.1.0 folder package |
| [`context-validator`](skills/context-validator/SKILL.md) | Read-only structural checks (package / schema / integrity L1–L3); L4 never auto-PASS |
| [`context-importer`](skills/context-importer/SKILL.md) | Read-only restore of context + session **Receiver Understanding Report** |

Do **not** merge these into one mega-skill. Exporter writes packages; Validator judges structure; Importer consumes for takeover.

**CBHF** (ContextBridge Handoff Format) lives under [`spec/cbhf/`](spec/cbhf/) and [`skills/context-exporter/references/cbhf-format.md`](skills/context-exporter/references/cbhf-format.md). It is a **protocol**, not a Skill.

## CBHF 0.1.0 package layout

Exporter-required tree:

```text
<package-root>/
├── manifest.yaml
├── source/
│   ├── source-index.json
│   └── original/                 # package copies (may be redacted)
├── knowledge/
│   ├── overview.md
│   ├── facts.json
│   ├── claims.json
│   ├── decisions.json
│   ├── constraints.json
│   └── glossary.json
├── evidence/
│   ├── evidence.json
│   └── references.json
├── uncertainty/
│   ├── unknowns.json
│   └── conflicts.json
└── handoff/
    ├── receiver-guide.md
    ├── questions.json
    └── recommended-actions.json
```

Reserved path (CBHF 0.1.0: **session reports only**; in-package write **not enabled** — neither Exporter nor Validator creates it):

```text
<package-root>/validation/validation-report.json
```

Absence of `validation/` is normal in 0.1.0 and means **no packaged report** (usually not validated yet), not “validation passed”. Use the Validator **session** JSON as the authority.

## Quick start

1. Clone this repository and open it in an Agent Skills host (**Cursor** is the primary verified host).
2. Install discovery mirrors + check the environment:

```bash
python scripts/install_skills.py
pip install -r requirements-validator.txt
python scripts/doctor.py
```

3. Follow [docs/getting-started.md](docs/getting-started.md) for the demo. Host coverage: [docs/host-matrix.md](docs/host-matrix.md).
4. Explore the sample package: [`examples/technical-proposal/`](examples/technical-proposal/).

Path-invoke always works without install: point the agent at `skills/*/SKILL.md`.

Validator helper (optional, deterministic L1–L3), from the repo root:

```bash
python skills/context-validator/scripts/validate_package.py examples/technical-proposal/generated-output
```

Optional: `--schema-dir` pointing at a **local** `spec/cbhf/v0.1.0` (default). The script prints session JSON to stdout and does **not** modify the package. Exit code `1` only when `final_status` is `invalid`.

## End-to-end flow

```text
source docs  →  context-exporter  →  CBHF package
                                      ↓
                            context-validator (optional but recommended)
                                      ↓
                            context-importer  →  Receiver Understanding Report (session)
```

1. **Export** — agent follows `context-exporter` against your documents into a new package folder.
2. **Validate** — agent follows `context-validator` (prefer the helper script) for L1–L3 honesty.
3. **Import** — receiving agent follows `context-importer`, optionally with the Validator session JSON.

## Example: technical proposal

[`examples/technical-proposal/`](examples/technical-proposal/) is a **fictional** Northwind Edge Gateway corpus for demos and tests.

| Path | Meaning |
| --- | --- |
| `input/` | Synthetic source documents (**not** produced by Exporter). May contain **drill / fake** secret strings for redaction exercises — not real credentials. |
| `generated-output/` | A complete CBHF 0.1.0 package (redacted copies, knowledge, evidence, unknowns, one conflict). |
| `expected-output/EXPECTED.md` | Human expectations for the sample — not a second protocol. |

## Documentation map

| Doc | Audience |
| --- | --- |
| [docs/getting-started.md](docs/getting-started.md) | First run |
| [docs/README.md](docs/README.md) | Full index (user vs audit docs) |
| [cbhf-format.md](skills/context-exporter/references/cbhf-format.md) | Human CBHF field/layout guide |
| [spec/cbhf/v0.1.0/](spec/cbhf/v0.1.0/) | Machine JSON Schemas |
| Skill `SKILL.md` files under [`skills/`](skills/) | Agent instructions |

## Current capabilities and limits (v0.1.0)

**In scope / implemented**

- Three Skills with instructions for CBHF **0.1.0** folder packages (`docs` scenario).
- JSON Schemas under `spec/cbhf/v0.1.0/`.
- Validator helper automates L1, L2, and L3 integrity checks including path safety, locators, excerpt match (I14), and optional package_copy checksums (I20).
- Importer gates (unvalidated / invalid / force + `UNTRUSTED_STRUCTURE`) documented and E2E exercised.
- Sample package + schema/validator/importer acceptance materials under `examples/` and `tests/`.

**Out of scope / not claimed**

- L4 semantic review is **never** an automated PASS.
- No guarantee of identical behavior on every AI host; see [docs/host-matrix.md](docs/host-matrix.md). Cursor is the primary **verified** host; others may work via `.agents` / `.claude` discovery after `install_skills.py`.
- No Dashboard, database, MCP server product, ZIP sync, or cloud knowledge-base product in v0.1.0.
- Best-effort redaction ≠ complete secret/PII discovery.
- No invented performance, success-rate, or user-count metrics.

## Roadmap (indicative)

- Keep CBHF 0.1.0 stable; promote host-matrix rows from `unverified` → `verified` as other hosts are exercised.
- Optional packaged validation-report shape freeze (still Validator-owned).
- More importer/validator fixtures (e.g. `readable: false` demos) without changing frozen rules lightly.
- Clearer contribution guide after the first public tag.

## License

Licensed under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE).
