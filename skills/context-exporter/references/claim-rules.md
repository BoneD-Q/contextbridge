# Claim & status rules (CBHF 0.1.0)

Used by `context-exporter` when classifying knowledge items and assigning **KnowledgeStatus**.

- **Field shapes / shared types:** [cbhf-format.md](cbhf-format.md) (authority for schemas; do not fork field names here)
- **Evidence / locators / redaction practice:** [evidence-rules.md](evidence-rules.md)

This file does **not** redefine package layout. If a field shape here drifts from `cbhf-format.md`, fix this file.

## Object types

| Type | File | What it is | What it is not |
| --- | --- | --- | --- |
| **Fact** | `facts.json` | Descriptive atom from sources (“X is Y”) | Not a recommendation; not automatic truth |
| **Claim** | `claims.json` | Assertion/interpretation needing epistemology | Not a dump of whole paragraphs |
| **Decision** | `decisions.json` | A choice that was made (or claimed made) | Not a vague goal |
| **Constraint** | `constraints.json` | Requirement or prohibition | Not an observation |
| **Term** | `glossary.json` | Defined vocabulary | Not verified merely by being listed |
| **Unknown** | `unknowns.json` | Material gap the receiver must not invent | Not trivia |
| **Conflict** | `conflicts.json` | Same-subject, same-context, mutually exclusive pair | Not env/version mismatch |

### Extraction heuristics

1. Split compound sentences when statuses might differ.
2. Keep `statement.text` / `summary.text` / `definition.text` in the source language; translations only in `i18n`.
3. Fact + conclusion in one sentence → two records (fact + inferred claim) when needed.
4. Unreadable diagrams/binaries → Unknown — do not invent contents.
5. Fill optional `context` when environment/version/time/scope is stated or clearly implied.

### Presence ≠ verified

Creating a row in `facts.json`, `claims.json`, `decisions.json`, `constraints.json`, or `glossary.json` does **not** assign `verified`. Status is always explicit and earned.

---

## KnowledgeStatus values (closed set)

`verified` | `user_confirmed` | `inferred` | `unverified` | `unknown` | `disputed`

Same spelling everywhere (SKILL, format, evidence rules).

**Not** the same as `references[].status` (**ReferenceStatus** in cbhf-format), action `status` (`pending` \| `blocked` \| `cancelled`), or `manifest.validation`.

### Allowed statuses by object type

| Status | facts | claims | decisions | constraints | glossary terms |
| --- | --- | --- | --- | --- | --- |
| `verified` | yes | yes | yes | yes | yes |
| `user_confirmed` | yes | yes | yes | yes | yes |
| `inferred` | yes* | yes | yes* | yes* | yes* |
| `unverified` | yes | yes | yes | yes | yes |
| `unknown` | yes | yes | yes | yes | yes |
| `disputed` | yes | yes | yes | yes | yes |

\* Prefer moving pure interpretive leaps to **claims** with `inferred`. For facts/decisions/constraints/terms, use `inferred` only when the object type still fits but wording was not explicit (e.g. glossary definition synthesized from multiple spans).

### Per-type judgment notes

#### facts

- Prefer atoms that are explicitly stated.
- `verified` only with adequate evidence (see evidence-rules).
- `inferred` rare — if the leap is interpretive, emit a **claim** instead.
- Env-specific facts SHOULD set `context.environment` (e.g. prod vs test).

#### claims

- Default home for assertive/interpretive content.
- All six statuses common.
- `inferred` MUST include an `Inference:` note explaining the leap.

#### decisions

- `verified`: source explicitly records that the decision was made + adequate evidence.
- `user_confirmed`: user confirms **this decision** in-session (with `confirmation`).
- `inferred`: exporter infers a decision was made though sources only hint — label clearly; do not present as settled policy in overview.
- Mention of a future option ≠ decision.

#### constraints

- `verified` / `unverified` from sourced requirement text.
- `user_confirmed` when the user confirms that constraint applies.
- Soft wishes (“maybe we should”) are not `must` constraints; downgrade priority or use a claim.

#### glossary terms

- `verified`: definition (or equivalent) appears in sources with adequate evidence.
- `inferred`: exporter wrote a gloss not verbatim in sources.
- `unverified`: term appears but definition not pinned.
- `unknown`: term used but meaning not established — prefer also an Unknown row if material.
- **Never** default `verified` because a term was entered.

---

## Decision tree (all object types)

Apply in order; stop at first full match.

```
1. Is there a TRUE conflict with another item?
   (same subject AND context aligned AND mutually exclusive)
   YES → status disputed + conflicts.json entry; do not pick a winner.
   NO  → continue
   If subject/context alignment is UNCERTAIN → do NOT dispute yet;
   file a question/unknown instead; continue with other statuses.

2. Did the user explicitly confirm THIS proposition
   (not a guess/suggestion/uncertainty)?
   YES → user_confirmed + REQUIRED confirmation object
   NO  → continue

3. Explicitly present in sources AND adequate evidence+locator
   (and redaction did not destroy support)?
   YES → verified
   NO  → continue

4. Present in sources BUT evidence/locator inadequate
   (unread binary, weak locator, redaction damage, …)?
   YES → unverified
   NO  → continue

5. Reasonable conclusion not verbatim, grounded in cited premises?
   YES → inferred (notes explain leap; never sell as verified)
   NO  → continue

6. Needed for handoff but not established?
   YES → unknown (+ usually unknowns.json)
   NO  → do not emit the record
```

---

## Status definitions

### `verified`

- ≥1 adequate evidence item with concrete locator + excerpt inside the package copy.
- No reliance on outside knowledge or unread files.
- **Forbidden:** model prior, “common practice”, unfetched URLs, tests not run, unread PDF/DOCX/image claims.

### `user_confirmed`

- User explicitly affirmed **this specific proposition**.
- Guess / suggestion / “也许” / “我觉得可能” / brainstorming ≠ confirmation.
- AI inference must never be labeled `user_confirmed`.
- Silence ≠ confirmation.
- **Required field:** `confirmation` (see below).

### `inferred`

- Follows from sources but not stated verbatim.
- Link premise evidence when possible; `notes` include `Inference: …`.
- Must not be described as verified in overview / receiver-guide.

### `unverified`

- Said in sources (or user text) but not adequately pinned — including support lost to redaction.
- Receiver treats as “said somewhere, not pinned”.

### `unknown`

- Not established; material for continuing work.
- Prefer `unk_*` with `why_it_matters`.
- **Forbidden:** web fill or training-data guesses.

### `disputed`

- Only with a true Conflict (`cfl_*`) under the conflict rules below.
- `resolution` stays `null` until the user resolves it.

---

## `confirmation` object (`user_confirmed` only)

Required shape (normative shared type: cbhf-format `Confirmation`):

```json
{
  "confirmation": {
    "confirmed_by": "user",
    "source_type": "conversation",
    "source_ref": null,
    "confirmation_text": "用户明确确认的原话",
    "confirmed_at": null,
    "limitations": null
  }
}
```

| Field | Rule |
| --- | --- |
| `confirmed_by` | Always `user` in 0.1.0 for this status |
| `source_type` | `conversation` \| `user_authored_source` \| `other` (meanings below) |
| `source_ref` | Depends on `source_type` (table below) |
| `confirmation_text` | Exact wording for **this** proposition when retainable |
| `confirmed_at` | ISO-8601 UTC if known; else `null` |
| `limitations` | Required when `confirmation_text` is `null`/incomplete, or when `source_type` is `other` |

### `source_type` meanings

| Value | Meaning |
| --- | --- |
| `conversation` | User explicitly affirmed this proposition in the **current** agent session / chat |
| `user_authored_source` | Affirmation text lives in a **packaged** user-authored file (indexed `source_id`) |
| `other` | Affirmation is attributed to the user but arrived via a channel that is **neither** this session **nor** a packaged user-authored source (e.g. user forwards their own prior note; paste from an external ticket **without** packaging that ticket as a source). Must explain the channel in `confirmation.limitations`. Must **not** invent a fake `source_id`. |

### `source_ref` by `source_type`

| `source_type` | `source_ref` rule |
| --- | --- |
| `conversation` | `null`, or a privacy-safe host message id if available |
| `user_authored_source` | **MUST** be a `source_id` present in `source/source-index.json` |
| `other` | `null`, or a short **non-`src_*`** channel label; **MUST NOT** be a `source_id` that does not exist; prefer `null` + `limitations` over fabricating `src_*` |

Rules:

1. Confirm the proposition you store — not a vague adjacent topic.
2. If the user confirms only part of a compound statement, split atoms; confirm only the affirmed atom.
3. Guess / suggestion / uncertainty from the user ≠ confirmation (any `source_type`).
4. AI inference must never receive `user_confirmed`.
5. If exact wording cannot be retained, set `confirmation_text: null` and explain in `limitations` (also mention in `manifest.limitations` when systemic).
6. For `user_authored_source`, still prefer packaging/quoting that confirmation span as evidence (`kind: user_message` or excerpt) when possible.
7. For `other`, do not silently upgrade trust: keep honest `limitations`; attach evidence only if a real packaged span exists.
8. For non-`user_confirmed` statuses, set `"confirmation": null` (prefer explicit `null`).

---

## Mapping examples

| Situation | Typical status |
| --- | --- |
| “生产端口为 8080” + line locator | `verified` (fact, `context.environment: prod`) |
| User: “对，生产就是 8080” | `user_confirmed` + `confirmation` |
| User: “也许端口是 8080吧” | not confirmation → likely `unverified`/`unknown` or ignore |
| Latency table → “瓶颈在连接池” | `inferred` claim |
| Unread scanned PDF assertion | `unverified` or `unknown` + limitation |
| Test:8000 vs Prod:8080 | **not** a conflict; two facts with different `context` |
| Two prod docs: 8080 vs 8000 | `disputed` + conflict |
| Glossary term coined by exporter | `inferred` term |
| “副本数 TBD” | `unknown` |

---

## Forbidden upgrades

| From | To | Allowed? |
| --- | --- | --- |
| `inferred` | `verified` | Only with new explicit excerpt support |
| `inferred` | `user_confirmed` | Only after explicit user confirmation of that proposition |
| `unverified` | `verified` | Only after adequate locator/evidence (post-redaction still adequate) |
| `disputed` | other | Only after user resolution recorded |
| `unknown` | `verified` | Only with new sourced evidence — never by guessing |

Never majority-vote conflicts. Never delete one side to “clean” the package.

---

## Facts vs claims vs decisions vs constraints vs terms

Gate:

1. Rule/requirement? → **constraint**  
2. Chosen option among alternatives? → **decision**  
3. Vocabulary definition? → **term**  
4. Bare descriptive atom? → **fact**  
5. Otherwise assertive/interpretive? → **claim**  

If unsure between fact and claim, prefer **claim** with conservative status.  
Do not duplicate the same sentence across all files.

---

## Conflicts (strict)

### Create a Conflict only when ALL hold

1. **Same subject** — both statements are about the same object of discourse.  
2. **Context aligned** — environment / version / time / scope are the same or explicitly identical (`context_alignment: same`).  
3. **Mutually exclusive** — they cannot both be true under that context.

### Do NOT create a Conflict when

- Environments differ (test `8000` vs prod `8080`)  
- Versions/time ranges differ and both can be historically true  
- Wording differs but meaning is compatible  
- Context alignment is **uncertain**

### When context is uncertain

- Do **not** write `conflicts.json` for that pair.
- Add `questions.json` (and optionally `unknowns.json` + `recommended-actions.json`).
- Keep each statement at the best non-`disputed` status it independently earns (`verified` / `unverified` / …).
- Optionally note the potential tension in `notes` without declaring `disputed`.

### When a true Conflict exists

1. Emit `cfl_*` with `same_subject: true`, `context_alignment: same`, `shared_context`, parties, evidence.  
2. Set involved items to `disputed` and link `conflict_ids`.  
3. Add `q_*` / `act_*` (`pending`) for user resolution.  
4. Leave `resolution: null` until the user resolves.

---

## Unknowns

Create when missing information would likely cause invention:

- Env-specific values not in docs  
- Owners / on-call  
- Whether a feature shipped  
- Content inside unread binaries  
- Confirmations lacking retainable text when that absence blocks trust  

Do not spam trivia.

---

## Bilingual fidelity

- Preserve epistemic force in translations (“可能” must not become “is”).
- Unsafe to translate → leave target empty + `manifest.limitations`.

---

## Redaction interaction

If redaction removes or alters the only supporting excerpt / locator adequacy:

1. Do **not** keep `verified`.  
2. Downgrade to `unverified`, or Unknown if the content is no longer usable.  
3. Never re-expand secrets to preserve verification.  
4. Record in evidence `notes` / `redaction_applied` and manifest redaction limitations (best-effort, not complete discovery).
