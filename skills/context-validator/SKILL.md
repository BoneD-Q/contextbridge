---
name: context-validator
description: Validate a CBHF handover package for structure, provenance, evidence, citations, conflicts, and file integrity. Use when checking ContextBridge packages before import or distribution. Optional Python helpers may live under scripts/.
license: Apache-2.0
metadata:
  author: contextbridge
  version: "0.1.0"
  protocol: CBHF
---

# context-validator

> Status: skeleton — full instructions not implemented yet.

## Purpose

Check that a CBHF handover package is structurally sound and that sources, evidence, citations, conflicts, and file integrity meet the protocol rules.

## Inputs / Outputs

- **Inputs:** a CBHF handover package (to be specified)
- **Outputs:** a validation report (to be specified)

## Scripts

Optional Python helpers may be placed under `scripts/` for deterministic checks. They are aids, not a standalone application.

## References

See `references/` for validation checklists once authored. Protocol definition lives in `spec/cbhf/`.
