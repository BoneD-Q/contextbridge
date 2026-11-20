# Documentation index

ContextBridge documentation falls into two buckets. Prefer **user docs** for demos and public onboarding. Keep **development / audit** docs as historical engineering records — do not treat them as a second CBHF specification.

## A. User documentation

| Doc | Purpose |
| --- | --- |
| [Getting started](getting-started.md) | First end-to-end demo + skill install |
| [Host matrix](host-matrix.md) | Discovery / verified vs unverified hosts |
| [Root README (EN)](../README.md) / [中文](../README.zh-CN.md) | Product overview, skills, limits |
| [CBHF format (human)](../skills/context-exporter/references/cbhf-format.md) | Package layout and field semantics |
| [CBHF schemas](../spec/cbhf/v0.1.0/) | Machine-readable Draft 2020-12 JSON Schemas |
| [context-exporter SKILL](../skills/context-exporter/SKILL.md) | Export instructions (+ claim/evidence references) |
| [context-validator SKILL](../skills/context-validator/SKILL.md) | Validate instructions (+ validation-rules / report-format / L4 boundary) |
| [context-importer SKILL](../skills/context-importer/SKILL.md) | Import instructions (+ import/trust/report references) |
| [Example: technical-proposal](../examples/technical-proposal/) | Sample input + generated CBHF package |

Related Exporter references (user/protocol):

- [`claim-rules.md`](../skills/context-exporter/references/claim-rules.md)
- [`evidence-rules.md`](../skills/context-exporter/references/evidence-rules.md)

## B. Development and audit documentation

These files record Validator design and rule freezes. They may lag UI polish; **protocol authority** remains `cbhf-format.md` + `spec/cbhf/v0.1.0/` + frozen Skill references.

| Doc | Purpose |
| --- | --- |
| [context-validator-design.zh-CN.md](context-validator-design.zh-CN.md) | Validator design notes |
| [validator-l3-implementation-plan.zh-CN.md](validator-l3-implementation-plan.zh-CN.md) | L3 implementation plan / status |
| [validator-i14-test-plan.zh-CN.md](validator-i14-test-plan.zh-CN.md) | I14 excerpt-match test plan |
| [validator-i20-audit.zh-CN.md](validator-i20-audit.zh-CN.md) | I20 read-only audit |
| [validator-i20-decision-draft.zh-CN.md](validator-i20-decision-draft.zh-CN.md) | I20 decision draft (historical) |
| [Semantic review corpus](../tests/semantic-review/v0.1.0/) | Manual L4-oriented review artifacts |
| [Validator E2E](../tests/validator/e2e/) | Skill E2E acceptance materials |
| [Importer E2E](../tests/importer/e2e/) | Importer E2E acceptance materials |
| Schema / smoke tests | [`../tests/schema/v0.1.0/`](../tests/schema/v0.1.0/) |
| Validator regression tests | [`../tests/validator/v0.1.0/`](../tests/validator/v0.1.0/) |

## What not to invent

- Do not add a parallel “cbhf-specification.md” that forks field names from `cbhf-format.md` / schemas.
- Do not rewrite audit docs into marketing claims.
- Do not present smoke tests as formal Validator certification.
