# Northwind Edge Gateway — Architecture Overview (Draft)

Document status: working draft for handoff testing  
Product: Northwind Edge Gateway  
Audience: platform + edge ops

## 1. Purpose

Northwind Edge Gateway terminates TLS at edge PoPs and routes HTTP/1.1 and HTTP/2 traffic to regional origin pools.

## 2. Established facts (from this design note)

1. The control-plane API listens on path prefix `/v1/admin`.
2. Data-plane health checks use `GET /healthz` and expect HTTP 200.
3. Default idle timeout for upstream connections is **60 seconds**.
4. Supported TLS versions are **TLS 1.2 and TLS 1.3** only.
5. Configuration is stored as versioned YAML objects in the control store; object id format is `cfg_<uuid>`.

## 3. Constraints

1. Must not introduce a standalone public Web UI in v1 (API and CLI only).
2. Must not store raw customer request bodies in edge logs by default.
3. Production changes require a change ticket id in the deploy annotation.

## 4. Technical conclusion (inferred from latency table below)

In the last internal soak test summary embedded here, P99 latency rose when the upstream connection pool was saturated while CPU remained under 40%. From that pattern, the working conclusion is:

> The current bottleneck is the **upstream connection pool**, not CPU.

This conclusion is an **interpretation** of the soak numbers; it is not a verbatim measurement label in the table.

### Soak excerpt

| Metric | Value |
| --- | --- |
| CPU avg | 38% |
| Conn pool wait P99 | 120 ms |
| Handler time P99 | 15 ms |

## 5. Glossary seeds

- **PoP**: Point of Presence — an edge location running gateway instances.
- **Origin pool**: Set of regional backends selected by routing policy.

## 6. Sensitive material (for redaction drills)

A staging bootstrap example (must be redacted in any handoff package):

```
EDGE_BOOTSTRAP_TOKEN=[REDACTED:token]
DB_PASSWORD=[REDACTED:password]
```

Operators must rotate these after any accidental share.

# E2E tamper for I20 checksum mismatch

