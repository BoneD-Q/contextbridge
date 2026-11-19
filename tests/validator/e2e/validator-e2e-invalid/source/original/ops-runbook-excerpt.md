# Ops runbook excerpt — Northwind Edge Gateway

Environment labels used in this excerpt: `prod` and `staging` only.

## Production listen port

For **production** (`environment: prod`) edge data-plane processes:

> Production data-plane listen port is **8080**.

Source note: copied from prod systemd unit `edge-gw.service` review on 2026-10-02.

## Staging listen port

For **staging** (`environment: staging`):

> Staging data-plane listen port is **8000**.

These two statements are **not** a conflict: different environments.

## Production port contradiction (same context)

A later paragraph in the same runbook (also labeled **production** / `environment: prod`) states:

> Production data-plane listen port is **8000**.

This second production statement **cannot** both be true with the earlier production `8080` statement under the same environment and scope (edge data-plane listen port). A handoff package should record a **Conflict**, not silently pick one.

## Deploy annotation

Production deploys must include annotation:

`change_ticket=<TICKET-ID>`

Example (non-secret): `change_ticket=CHG-10422`

## Credential material (redact)

Pager webhook (staging):

```
PAGER_WEBHOOK_URL=[REDACTED:token]
```
