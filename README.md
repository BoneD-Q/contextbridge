# ContextBridge

**Agent Skills for lossless AI-to-AI document handoff.**

ContextBridge is an open-source **Agent Skills** project — not a standalone Python app or web service. It addresses a common failure mode: when one AI produces a document for another AI, context, evidence, decisions, and unknowns are often lost.

## What it is

Three independent Skills share one data protocol:

| Skill | Role |
| --- | --- |
| [`context-exporter`](skills/context-exporter/) | Turn source documents into a CBHF handover package |
| [`context-validator`](skills/context-validator/) | Check package structure, provenance, evidence, citations, conflicts, and integrity |
| [`context-importer`](skills/context-importer/) | Read a package, restore context, and produce a takeover understanding report |

**CBHF** (ContextBridge Handoff Format) is the shared data protocol under [`spec/cbhf/`](spec/cbhf/). It is not a Skill.

## Repository layout

```
skills/          # Agent Skills (SKILL.md + optional scripts/references)
spec/cbhf/       # CBHF protocol versions
examples/        # End-to-end sample inputs and expected outputs
tests/           # Protocol and skill-oriented tests
```

Python appears only as **optional helper scripts** for the validator — not as an application runtime.

## Status

v0 skeleton: directory layout and Skill stubs only. Full Skill instructions, CBHF schema, examples, and tests are forthcoming.

## License

Apache-2.0 (planned; license file to be added with the first substantive release).

---

[中文说明](README.zh-CN.md)
