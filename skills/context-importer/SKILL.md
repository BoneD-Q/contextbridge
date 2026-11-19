---
name: context-importer
description: Read a CBHF handover package, restore working context, and produce a takeover understanding report. Use when an agent inherits a ContextBridge package and needs to continue the work.
license: Apache-2.0
metadata:
  author: contextbridge
  version: "0.1.0"
  protocol: CBHF
---

# context-importer

> Status: skeleton — full instructions not implemented yet.

## Purpose

Consume a CBHF handover package, restore preserved context for the receiving agent, and generate a takeover understanding report.

## Inputs / Outputs

- **Inputs:** a CBHF handover package (to be specified)
- **Outputs:** restored context plus a takeover understanding report (to be specified)

## References

See `references/` for import/report guidance once authored. Protocol definition lives in `spec/cbhf/`.
