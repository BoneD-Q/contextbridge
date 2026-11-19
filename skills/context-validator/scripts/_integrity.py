"""L3 Integrity helpers for context-validator.

Phase 3B-1 implements Batch A (cross-file reference existence) only:
I01–I09, I15, I17, I18, I19.

I10–I14, I16, I20 remain NOT_CHECKED until later batches.
L4 is never automated here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Status strings mirror validate_package.py
PASS = "PASS"
FAIL = "FAIL"
WARNING = "WARNING"
NOT_CHECKED = "NOT_CHECKED"

L3A_IDS = {
    "I01",
    "I02",
    "I03",
    "I04",
    "I05",
    "I06",
    "I07",
    "I08",
    "I09",
    "I15",
    "I17",
    "I18",
    "I19",
}

L3_DEFERRED_IDS = {
    "I10": "Phase 3B-1: L3-B path existence not implemented",
    "I11": "Phase 3B-1: L3-B path safety not implemented",
    "I12": "Phase 3B-1: L3-B line_range bounds not implemented",
    "I13": "Phase 3B-1: L3-B other locator findability not implemented (Q2)",
    "I14": "Phase 3B-1: L3-C excerpt match not implemented",
    "I16": "Phase 3B-1: L3-B readable:false rule not implemented",
    "I20": "Phase 3B-1: checksum verification not implemented (Q3)",
}

# kind -> (relative file, array key, id field, schema check id)
KIND_SPECS: list[tuple[str, str, str, str, str]] = [
    ("source", "source/source-index.json", "sources", "source_id", "S03"),
    ("fact", "knowledge/facts.json", "facts", "fact_id", "S04"),
    ("claim", "knowledge/claims.json", "claims", "claim_id", "S05"),
    ("decision", "knowledge/decisions.json", "decisions", "decision_id", "S06"),
    ("constraint", "knowledge/constraints.json", "constraints", "constraint_id", "S07"),
    ("term", "knowledge/glossary.json", "terms", "term_id", "S08"),
    ("evidence", "evidence/evidence.json", "evidence", "evidence_id", "S09"),
    ("reference", "evidence/references.json", "references", "reference_id", "S10"),
    ("unknown", "uncertainty/unknowns.json", "unknowns", "unknown_id", "S11"),
    ("conflict", "uncertainty/conflicts.json", "conflicts", "conflict_id", "S12"),
    ("question", "handoff/questions.json", "questions", "question_id", "S13"),
    ("action", "handoff/recommended-actions.json", "actions", "action_id", "S14"),
]

KNOWLEDGE_KINDS = ("fact", "claim", "decision", "constraint", "term")
SUPPORT_TYPES = set(KNOWLEDGE_KINDS)

REL_MANIFEST = "manifest.yaml"
REL_SOURCE = "source/source-index.json"
REL_EVIDENCE = "evidence/evidence.json"
REL_CONFLICTS = "uncertainty/conflicts.json"
REL_QUESTIONS = "handoff/questions.json"
REL_ACTIONS = "handoff/recommended-actions.json"
REL_UNKNOWNS = "uncertainty/unknowns.json"


@dataclass
class CheckOut:
    id: str
    name: str
    result: str
    message: str = ""
    path: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PackageIndex:
    """In-memory indexes built from L1-parsed objects (schema-ok files only)."""

    by_kind: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded_kinds: set[str] = field(default_factory=set)
    skipped_files: dict[str, str] = field(default_factory=dict)  # rel -> reason
    all_ids: set[str] = field(default_factory=set)
    package_ids: list[str] = field(default_factory=list)
    # True only when every KIND_SPECS collection is schema-ok loaded.
    all_ids_complete: bool = False


def _schema_ok(schema_results: dict[str, str], sid: str) -> bool:
    return schema_results.get(sid) == PASS


def build_package_index(
    parsed_objects: dict[str, Any],
    parse_ok: dict[str, bool],
    schema_results: dict[str, str],
    manifest_obj: Any | None,
) -> PackageIndex:
    idx = PackageIndex()
    for kind, rel, array_key, id_field, schema_id in KIND_SPECS:
        if not parse_ok.get(rel):
            idx.skipped_files[rel] = "not parseable in L1"
            continue
        if not _schema_ok(schema_results, schema_id):
            status = schema_results.get(schema_id, NOT_CHECKED)
            idx.skipped_files[rel] = f"schema {schema_id} is {status}"
            continue
        doc = parsed_objects.get(rel)
        if not isinstance(doc, dict):
            idx.skipped_files[rel] = "parsed object is not a dict"
            continue
        items = doc.get(array_key)
        if not isinstance(items, list):
            idx.skipped_files[rel] = f"missing array {array_key}"
            continue
        bucket: dict[str, Any] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            oid = item.get(id_field)
            if isinstance(oid, str):
                # Keep first; duplicates detected in I01
                if oid not in bucket:
                    bucket[oid] = item
                idx.all_ids.add(oid)
        idx.by_kind[kind] = bucket
        idx.loaded_kinds.add(kind)

    if parse_ok.get(REL_MANIFEST) and isinstance(manifest_obj, dict):
        pid = manifest_obj.get("package_id")
        if isinstance(pid, str):
            idx.package_ids.append(pid)
            idx.all_ids.add(pid)
    elif not parse_ok.get(REL_MANIFEST):
        idx.skipped_files[REL_MANIFEST] = "manifest not parseable"

    expected_kinds = {spec[0] for spec in KIND_SPECS}
    idx.all_ids_complete = expected_kinds <= idx.loaded_kinds
    return idx


def path_form_forbidden(rel: str) -> bool:
    """Reject absolute, drive, UNC, and .. forms (report_path safety)."""
    if not isinstance(rel, str) or rel == "":
        return True
    normalized = rel.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("//"):
        return True
    if len(rel) >= 2 and rel[1] == ":":
        return True
    p = Path(rel)
    if p.is_absolute():
        return True
    if ".." in p.parts:
        return True
    return False


def classify_package_rel_file(package: Path, rel: str) -> tuple[str, str]:
    """Classify a package-relative file path.

    Returns (code, message) where code is exists | missing | unsafe.
    Does not follow escaping symlinks as a successful locate.
    """
    if path_form_forbidden(rel):
        return "unsafe", f"forbidden report_path form: {rel!r}"
    root = package.resolve()
    candidate = package / rel
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root)
    except (ValueError, OSError) as exc:
        return "unsafe", f"report_path escapes package root or cannot resolve: {exc}"
    # Intermediate symlink escape already caught by resolve+relative_to.
    if resolved.is_file():
        return "exists", ""
    return "missing", f"report file not found at {rel}"


def _knowledge_loaded(idx: PackageIndex) -> bool:
    return all(k in idx.loaded_kinds for k in KNOWLEDGE_KINDS)


def _evidence_loaded(idx: PackageIndex) -> bool:
    return "evidence" in idx.loaded_kinds


def _source_loaded(idx: PackageIndex) -> bool:
    return "source" in idx.loaded_kinds


def check_i01(idx: PackageIndex, parsed_objects: dict[str, Any], parse_ok: dict[str, bool], schema_results: dict[str, str]) -> CheckOut:
    """Duplicate IDs within each kind namespace.

    - Confirmed duplicates among loaded collections → FAIL
    - No confirmed duplicates but not all applicable collections loaded → NOT_CHECKED
    - All applicable collections loaded and no duplicates → PASS
    Cross-kind identical strings remain allowed.
    """
    name = "Duplicate IDs"
    applicable = list(KIND_SPECS)
    loaded_any = bool(idx.loaded_kinds)
    if not loaded_any and not (
        parse_ok.get(REL_MANIFEST) and _schema_ok(schema_results, "S02")
    ):
        return CheckOut("I01", name, NOT_CHECKED, "no id-bearing collections loaded")

    errors: list[dict[str, str]] = []
    for kind, rel, array_key, id_field, _schema_id in applicable:
        if kind not in idx.loaded_kinds:
            continue
        doc = parsed_objects.get(rel)
        if not isinstance(doc, dict):
            continue
        seen: dict[str, int] = {}
        for i, item in enumerate(doc.get(array_key) or []):
            if not isinstance(item, dict):
                continue
            oid = item.get(id_field)
            if not isinstance(oid, str):
                continue
            if oid in seen:
                errors.append(
                    {
                        "path": f"{rel}#{array_key}/{i}/{id_field}",
                        "message": f"duplicate {id_field}={oid!r} (kind={kind})",
                    }
                )
            else:
                seen[oid] = i

    if errors:
        return CheckOut(
            "I01",
            name,
            FAIL,
            f"{len(errors)} duplicate id(s) within kind namespace(s)",
            errors=errors[:50],
        )

    missing_kinds = [spec[0] for spec in applicable if spec[0] not in idx.loaded_kinds]
    if missing_kinds:
        return CheckOut(
            "I01",
            name,
            NOT_CHECKED,
            "no confirmed duplicates, but applicable id collections not fully loaded: "
            + ", ".join(missing_kinds),
        )
    return CheckOut("I01", name, PASS, "all applicable id collections checked; no duplicates")


def check_i02(idx: PackageIndex) -> CheckOut:
    name = "evidence.supports → knowledge exists"
    if not _evidence_loaded(idx):
        return CheckOut("I02", name, NOT_CHECKED, "evidence.json not loaded for integrity")
    if not _knowledge_loaded(idx):
        return CheckOut(
            "I02",
            name,
            NOT_CHECKED,
            "one or more knowledge files not loaded for integrity",
        )

    errors: list[dict[str, str]] = []
    for eid, ev in idx.by_kind["evidence"].items():
        for j, sup in enumerate(ev.get("supports") or []):
            if not isinstance(sup, dict):
                continue
            typ = sup.get("type")
            sid = sup.get("id")
            if typ not in SUPPORT_TYPES:
                errors.append(
                    {
                        "path": f"{REL_EVIDENCE}#evidence/{eid}/supports/{j}",
                        "message": f"unknown supports.type={typ!r}",
                    }
                )
                continue
            bucket = idx.by_kind.get(typ, {})
            if sid not in bucket:
                errors.append(
                    {
                        "path": f"{REL_EVIDENCE}#evidence/{eid}/supports/{j}",
                        "message": f"supports missing {typ}:{sid}",
                    }
                )
    if errors:
        return CheckOut("I02", name, FAIL, f"{len(errors)} dangling supports link(s)", errors=errors[:50])
    return CheckOut("I02", name, PASS, "all evidence.supports resolve to knowledge objects")


def check_i03(idx: PackageIndex) -> CheckOut:
    name = "knowledge.evidence_ids → evidence exists"
    if not _evidence_loaded(idx):
        return CheckOut("I03", name, NOT_CHECKED, "evidence.json not loaded for integrity")
    if not _knowledge_loaded(idx):
        return CheckOut(
            "I03",
            name,
            NOT_CHECKED,
            "one or more knowledge files not loaded for integrity",
        )

    errors: list[dict[str, str]] = []
    evidence_ids = idx.by_kind["evidence"]
    for kind in KNOWLEDGE_KINDS:
        for kid, obj in idx.by_kind[kind].items():
            for j, eid in enumerate(obj.get("evidence_ids") or []):
                if eid not in evidence_ids:
                    errors.append(
                        {
                            "path": f"knowledge/{kind}/{kid}/evidence_ids/{j}",
                            "message": f"{kid} evidence_ids unknown {eid}",
                        }
                    )
    if errors:
        return CheckOut("I03", name, FAIL, f"{len(errors)} dangling evidence_ids", errors=errors[:50])
    return CheckOut("I03", name, PASS, "all knowledge.evidence_ids resolve")


def check_i04(idx: PackageIndex) -> CheckOut:
    name = "Bidirectional evidence ↔ knowledge"
    if not _evidence_loaded(idx) or not _knowledge_loaded(idx):
        return CheckOut(
            "I04",
            name,
            NOT_CHECKED,
            "evidence or knowledge not loaded (I02/I03 prerequisites)",
        )

    errors: list[dict[str, str]] = []
    evidence = idx.by_kind["evidence"]

    for eid, ev in evidence.items():
        for j, sup in enumerate(ev.get("supports") or []):
            if not isinstance(sup, dict):
                continue
            typ, sid = sup.get("type"), sup.get("id")
            if typ not in SUPPORT_TYPES:
                continue
            obj = idx.by_kind.get(typ, {}).get(sid)
            if obj is None:
                continue  # reported by I02
            if eid not in (obj.get("evidence_ids") or []):
                errors.append(
                    {
                        "path": f"{REL_EVIDENCE}#{eid}/supports/{j}",
                        "message": f"{eid} not listed in {sid}.evidence_ids",
                    }
                )

    for kind in KNOWLEDGE_KINDS:
        for kid, obj in idx.by_kind[kind].items():
            for j, eid in enumerate(obj.get("evidence_ids") or []):
                ev = evidence.get(eid)
                if ev is None:
                    continue  # I03
                ok = any(
                    isinstance(s, dict) and s.get("id") == kid and s.get("type") == kind
                    for s in (ev.get("supports") or [])
                )
                if not ok:
                    errors.append(
                        {
                            "path": f"knowledge/{kind}/{kid}/evidence_ids/{j}",
                            "message": f"{kid} missing reverse supports in {eid}",
                        }
                    )

    if errors:
        return CheckOut("I04", name, FAIL, f"{len(errors)} one-way link(s)", errors=errors[:50])
    return CheckOut("I04", name, PASS, "supports and evidence_ids are symmetric")


def check_i05(idx: PackageIndex) -> CheckOut:
    name = "conflict.parties exist"
    if "conflict" not in idx.loaded_kinds:
        return CheckOut("I05", name, NOT_CHECKED, "conflicts.json not loaded")
    if not _knowledge_loaded(idx):
        return CheckOut("I05", name, NOT_CHECKED, "knowledge files not loaded")

    errors: list[dict[str, str]] = []
    for cid, cfl in idx.by_kind["conflict"].items():
        for j, party in enumerate(cfl.get("parties") or []):
            if not isinstance(party, dict):
                continue
            typ, pid = party.get("type"), party.get("id")
            bucket = idx.by_kind.get(typ or "", {})
            if pid not in bucket:
                errors.append(
                    {
                        "path": f"{REL_CONFLICTS}#{cid}/parties/{j}",
                        "message": f"{cid} party missing {typ}:{pid}",
                    }
                )
    if errors:
        return CheckOut("I05", name, FAIL, f"{len(errors)} missing conflict party(ies)", errors=errors[:50])
    return CheckOut("I05", name, PASS, "all conflict parties resolve")


def check_i06(idx: PackageIndex) -> CheckOut:
    name = "conflict.evidence_ids exist"
    if "conflict" not in idx.loaded_kinds:
        return CheckOut("I06", name, NOT_CHECKED, "conflicts.json not loaded")
    if not _evidence_loaded(idx):
        return CheckOut("I06", name, NOT_CHECKED, "evidence.json not loaded")

    errors: list[dict[str, str]] = []
    evidence = idx.by_kind["evidence"]
    for cid, cfl in idx.by_kind["conflict"].items():
        for j, eid in enumerate(cfl.get("evidence_ids") or []):
            if eid not in evidence:
                errors.append(
                    {
                        "path": f"{REL_CONFLICTS}#{cid}/evidence_ids/{j}",
                        "message": f"{cid} evidence_ids unknown {eid}",
                    }
                )
    if errors:
        return CheckOut("I06", name, FAIL, f"{len(errors)} dangling conflict evidence_ids", errors=errors[:50])
    return CheckOut("I06", name, PASS, "all conflict.evidence_ids resolve")


def check_i07(idx: PackageIndex) -> CheckOut:
    """Cross related_* / conflict_ids existence.

    Typed refs: FAIL only when target kind is loaded and id missing;
    target kind unloaded → incomplete (NOT_CHECKED), never pretend missing.

    Untyped related_ids (L3-RQ1): FAIL only when all_ids_complete and id absent;
    incomplete global index → NOT_CHECKED (id may live in unloaded collection).
    """
    name = "Cross related_* / conflict_ids exist"
    if not any(
        k in idx.loaded_kinds
        for k in (
            "question",
            "action",
            "unknown",
            "claim",
            "fact",
            "decision",
            "constraint",
            "term",
        )
    ):
        return CheckOut("I07", name, NOT_CHECKED, "no referring collections loaded")

    hard_errors: list[dict[str, str]] = []
    incomplete: list[dict[str, str]] = []

    def require_typed(target_kind: str, ref_id: str, path: str) -> None:
        if target_kind not in idx.loaded_kinds:
            incomplete.append(
                {
                    "path": path,
                    "message": f"target kind {target_kind} not loaded; cannot resolve {ref_id}",
                }
            )
            return
        if ref_id not in idx.by_kind[target_kind]:
            hard_errors.append(
                {"path": path, "message": f"missing {target_kind} id {ref_id}"}
            )

    def require_untyped(ref_id: str, path: str) -> None:
        if ref_id in idx.all_ids:
            return
        if not idx.all_ids_complete:
            incomplete.append(
                {
                    "path": path,
                    "message": (
                        f"related_ids {ref_id!r} not in loaded id set; "
                        f"global id index incomplete (all_ids_complete=false; L3-RQ1)"
                    ),
                }
            )
            return
        hard_errors.append(
            {
                "path": path,
                "message": (
                    f"related_ids unknown {ref_id} "
                    f"(global id index complete; L3-RQ1 full-set search)"
                ),
            }
        )

    if "question" in idx.loaded_kinds:
        for qid, q in idx.by_kind["question"].items():
            for j, cid in enumerate(q.get("related_conflict_ids") or []):
                require_typed(
                    "conflict", cid, f"{REL_QUESTIONS}#{qid}/related_conflict_ids/{j}"
                )
            for j, uid in enumerate(q.get("related_unknown_ids") or []):
                require_typed(
                    "unknown", uid, f"{REL_QUESTIONS}#{qid}/related_unknown_ids/{j}"
                )

    if "claim" in idx.loaded_kinds:
        for kid, obj in idx.by_kind["claim"].items():
            for j, fid in enumerate(obj.get("related_fact_ids") or []):
                require_typed(
                    "fact", fid, f"knowledge/claims.json#{kid}/related_fact_ids/{j}"
                )

    for kind in KNOWLEDGE_KINDS:
        if kind not in idx.loaded_kinds:
            continue
        for kid, obj in idx.by_kind[kind].items():
            for j, cid in enumerate(obj.get("conflict_ids") or []):
                require_typed(
                    "conflict", cid, f"knowledge/{kind}/{kid}/conflict_ids/{j}"
                )

    if "unknown" in idx.loaded_kinds:
        for uid, obj in idx.by_kind["unknown"].items():
            for j, rid in enumerate(obj.get("related_ids") or []):
                require_untyped(rid, f"{REL_UNKNOWNS}#{uid}/related_ids/{j}")

    if "action" in idx.loaded_kinds:
        for aid, obj in idx.by_kind["action"].items():
            for j, rid in enumerate(obj.get("related_ids") or []):
                require_untyped(rid, f"{REL_ACTIONS}#{aid}/related_ids/{j}")

    if hard_errors:
        return CheckOut(
            "I07",
            name,
            FAIL,
            f"{len(hard_errors)} related_* / conflict_ids miss(es)",
            errors=hard_errors[:50],
        )
    if incomplete:
        return CheckOut(
            "I07",
            name,
            NOT_CHECKED,
            "related_* cannot be fully resolved (target or global id index incomplete)",
            errors=incomplete[:20],
        )
    completeness = (
        "all_ids_complete=true" if idx.all_ids_complete else "all_ids_complete=false"
    )
    return CheckOut(
        "I07",
        name,
        PASS,
        f"related_* and conflict_ids resolve ({completeness})",
    )


def check_i08(idx: PackageIndex) -> CheckOut:
    name = "confirmation.source_ref for user_authored_source"
    if not _source_loaded(idx):
        return CheckOut("I08", name, NOT_CHECKED, "source-index not loaded")
    if not _knowledge_loaded(idx):
        return CheckOut("I08", name, NOT_CHECKED, "knowledge files not loaded")

    errors: list[dict[str, str]] = []
    sources = idx.by_kind["source"]
    for kind in KNOWLEDGE_KINDS:
        for kid, obj in idx.by_kind[kind].items():
            conf = obj.get("confirmation")
            if not isinstance(conf, dict):
                continue
            if conf.get("source_type") != "user_authored_source":
                continue
            ref = conf.get("source_ref")
            if not isinstance(ref, str) or ref not in sources:
                errors.append(
                    {
                        "path": f"knowledge/{kind}/{kid}/confirmation/source_ref",
                        "message": f"{kid} user_authored_source source_ref missing or unknown: {ref!r}",
                    }
                )
    if errors:
        return CheckOut("I08", name, FAIL, f"{len(errors)} invalid source_ref(s)", errors=errors[:50])
    return CheckOut(
        "I08",
        name,
        PASS,
        "user_authored_source source_ref values resolve (or none applicable)",
    )


def check_i09(idx: PackageIndex) -> CheckOut:
    name = "locator.source_id in source-index"
    if not _evidence_loaded(idx):
        return CheckOut("I09", name, NOT_CHECKED, "evidence.json not loaded")
    if not _source_loaded(idx):
        return CheckOut("I09", name, NOT_CHECKED, "source-index not loaded")

    errors: list[dict[str, str]] = []
    sources = idx.by_kind["source"]
    for eid, ev in idx.by_kind["evidence"].items():
        loc = ev.get("locator") or {}
        sid = loc.get("source_id") if isinstance(loc, dict) else None
        if sid not in sources:
            errors.append(
                {
                    "path": f"{REL_EVIDENCE}#{eid}/locator/source_id",
                    "message": f"{eid} unknown source_id {sid!r}",
                }
            )
    if errors:
        return CheckOut("I09", name, FAIL, f"{len(errors)} unknown locator.source_id(s)", errors=errors[:50])
    return CheckOut("I09", name, PASS, "all locator.source_id values resolve")


def check_i15(idx: PackageIndex) -> CheckOut:
    name = "verified ⇒ non-empty evidence_ids"
    if not _knowledge_loaded(idx):
        return CheckOut("I15", name, NOT_CHECKED, "knowledge files not loaded")

    errors: list[dict[str, str]] = []
    for kind in KNOWLEDGE_KINDS:
        for kid, obj in idx.by_kind[kind].items():
            if obj.get("status") != "verified":
                continue
            eids = obj.get("evidence_ids") or []
            if not eids:
                errors.append(
                    {
                        "path": f"knowledge/{kind}/{kid}/evidence_ids",
                        "message": f"{kid} verified without evidence_ids",
                    }
                )
    if errors:
        return CheckOut("I15", name, FAIL, f"{len(errors)} verified object(s) lack evidence_ids", errors=errors[:50])
    return CheckOut("I15", name, PASS, "all verified objects have non-empty evidence_ids")


def check_i17(schema_results: dict[str, str]) -> CheckOut:
    name = "content_transformed shape (schema-backed)"
    s03 = schema_results.get("S03", NOT_CHECKED)
    if s03 == PASS:
        return CheckOut(
            "I17",
            name,
            PASS,
            "content_transformed shape covered by S03 PASS",
            path=REL_SOURCE,
        )
    if s03 == FAIL:
        return CheckOut(
            "I17",
            name,
            NOT_CHECKED,
            "S03 failed; content_transformed not re-validated here",
            path=REL_SOURCE,
        )
    return CheckOut(
        "I17",
        name,
        NOT_CHECKED,
        "S03 not run; content_transformed shape not checked",
        path=REL_SOURCE,
    )


def check_i18(
    manifest_obj: Any | None,
    parse_ok: dict[str, bool],
    package: Path,
    schema_results: dict[str, str],
) -> CheckOut:
    """manifest.validation honesty with package-bounded report_path checks.

    Depends on S02 PASS. Does not judge report content semantics.
    Explicit report_path is authoritative — default path must not mask its absence.
    """
    name = "manifest.validation honesty"
    if not _schema_ok(schema_results, "S02"):
        return CheckOut(
            "I18",
            name,
            NOT_CHECKED,
            f"depends on S02 PASS; S02 is {schema_results.get('S02', NOT_CHECKED)}",
            path=REL_MANIFEST,
        )
    if not parse_ok.get(REL_MANIFEST) or not isinstance(manifest_obj, dict):
        return CheckOut("I18", name, NOT_CHECKED, "manifest not loaded")

    validation = manifest_obj.get("validation")
    if not isinstance(validation, dict):
        return CheckOut(
            "I18",
            name,
            FAIL,
            "manifest.validation missing or not an object",
            path=REL_MANIFEST,
        )

    present = validation.get("present")
    report_path = validation.get("report_path")

    if present is not True:
        return CheckOut(
            "I18",
            name,
            PASS,
            "validation.present is not true; consistent with absent or optional report",
            path=REL_MANIFEST,
        )

    # present == True
    if isinstance(report_path, str) and report_path.strip():
        code, detail = classify_package_rel_file(package, report_path)
        if code == "unsafe":
            return CheckOut(
                "I18",
                name,
                FAIL,
                detail,
                path=REL_MANIFEST,
                errors=[{"path": "manifest.yaml#validation/report_path", "message": detail}],
            )
        if code == "missing":
            return CheckOut(
                "I18",
                name,
                FAIL,
                f"validation.present=true but specified report_path missing: {report_path}",
                path=REL_MANIFEST,
                errors=[
                    {
                        "path": "manifest.yaml#validation/report_path",
                        "message": detail,
                    }
                ],
            )
        return CheckOut(
            "I18",
            name,
            PASS,
            f"validation.present=true and specified report_path exists: {report_path}",
            path=REL_MANIFEST,
        )

    # No explicit report_path → default location only
    default_rel = "validation/validation-report.json"
    code, detail = classify_package_rel_file(package, default_rel)
    if code == "unsafe":
        return CheckOut("I18", name, FAIL, detail, path=REL_MANIFEST)
    if code == "missing":
        return CheckOut(
            "I18",
            name,
            FAIL,
            "validation.present=true but default validation/validation-report.json not found",
            path=REL_MANIFEST,
        )
    return CheckOut(
        "I18",
        name,
        PASS,
        "validation.present=true and default validation report file present",
        path=REL_MANIFEST,
    )


def check_i19(idx: PackageIndex) -> CheckOut:
    name = "Orphan evidence (empty supports)"
    if not _evidence_loaded(idx):
        return CheckOut("I19", name, NOT_CHECKED, "evidence.json not loaded")

    orphans: list[dict[str, str]] = []
    for eid, ev in idx.by_kind["evidence"].items():
        supports = ev.get("supports")
        if not supports:
            orphans.append(
                {
                    "path": f"{REL_EVIDENCE}#{eid}/supports",
                    "message": f"{eid} has empty supports (allowed; prefer link)",
                }
            )
    if orphans:
        return CheckOut(
            "I19",
            name,
            WARNING,
            f"{len(orphans)} evidence item(s) with empty supports",
            errors=orphans[:50],
        )
    return CheckOut("I19", name, PASS, "no orphan evidence (all have non-empty supports)")


def run_l3_batch_a(
    *,
    package: Path,
    parsed_objects: dict[str, Any],
    parse_ok: dict[str, bool],
    schema_results: dict[str, str],
    manifest_obj: Any | None,
) -> list[CheckOut]:
    """Run L3-A checks and emit NOT_CHECKED stubs for deferred I* ids."""
    idx = build_package_index(parsed_objects, parse_ok, schema_results, manifest_obj)

    results: list[CheckOut] = [
        check_i01(idx, parsed_objects, parse_ok, schema_results),
        check_i02(idx),
        check_i03(idx),
        check_i04(idx),
        check_i05(idx),
        check_i06(idx),
        check_i07(idx),
        check_i08(idx),
        check_i09(idx),
        check_i15(idx),
        check_i17(schema_results),
        check_i18(manifest_obj, parse_ok, package, schema_results),
        check_i19(idx),
    ]

    deferred_names = {
        "I10": "locator.path exists",
        "I11": "Path safety",
        "I12": "line_range bounds",
        "I13": "Other locator types",
        "I14": "Excerpt text match",
        "I16": "readable:false sources",
        "I20": "Checksum (optional)",
    }
    for iid, reason in L3_DEFERRED_IDS.items():
        results.append(
            CheckOut(iid, deferred_names.get(iid, f"Integrity check {iid}"), NOT_CHECKED, reason)
        )

    # Stable order I01..I20
    order = {f"I{i:02d}": i for i in range(1, 21)}
    results.sort(key=lambda c: order.get(c.id, 99))
    return results
