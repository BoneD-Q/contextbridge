# Decision record — Northwind Edge Gateway

## DEC-01 — No standalone Web UI in v1

**Decision:** v1 ships API + CLI only; no standalone public Web UI.

**Rationale:** Reduces attack surface and keeps the first milestone focused on data-plane reliability.

**Status in source wording:** "We confirmed we will not ship a standalone Web UI in v1."

## DEC-02 — Folder handoff for ContextBridge pilot

**Decision:** Use CBHF **folder** package form for AI-to-AI handoff of this proposal set.

**Confirmation-style statement (treat as user-authored confirmation text when exporting):**

> 就按文件夹交接，不要做成单个 JSON 包。

## DEC-03 — TLS policy

**Decision:** Allow TLS 1.2 and TLS 1.3 only at the edge terminator.

Aligned with architecture-overview facts on supported TLS versions.
