#!/usr/bin/env python3
"""Phase 2 tests for context-validator L1+L2 (does not rename smoke)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills/context-validator/scripts/validate_package.py"
SCHEMA_DIR = ROOT / "spec/cbhf/v0.1.0"
GENERATED = ROOT / "examples/technical-proposal/generated-output"
FIXTURE_SCHEMA = ROOT / "tests/schema/v0.1.0"

sys.path.insert(0, str(SCRIPT.parent))
from validate_package import (  # noqa: E402
    fingerprint_package,
    validate_package,
)

PASSES = 0
FAILURES: list[str] = []


def ok(name: str) -> None:
    global PASSES
    PASSES += 1
    print(f"PASS {name}")


def fail(name: str, detail: str) -> None:
    FAILURES.append(f"{name}: {detail}")
    print(f"FAIL {name}: {detail}")


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        ok(name)
    else:
        fail(name, detail or "assertion failed")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump_json(path: Path, obj) -> None:
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def dump_yaml(path: Path, obj) -> None:
    write(path, yaml.safe_dump(obj, sort_keys=False, allow_unicode=True))


def minimal_manifest(**overrides):
    base = {
        "cbhf_version": "0.1.0",
        "protocol": "CBHF",
        "package_id": "pkg_validator_minimal",
        "title": {"zh": "最小校验包", "en": "Minimal validator package"},
        "scenario": "docs",
        "package_form": "folder",
        "generated_at": "2026-11-19T05:00:00Z",
        "generator": {"skill": "context-exporter", "skill_version": "0.1.0"},
        "locale": {"narratives": ["zh", "en"], "primary_source_lang": "zh"},
        "sources_summary": {"count": 1, "source_ids": ["src_001"]},
        "limitations": ["Test fixture only."],
        "redaction": {
            "applied": False,
            "policy": "default_secrets_and_pii",
            "completeness": "best_effort",
        },
        "validation": {"present": False, "report_path": None},
    }
    base.update(overrides)
    return base


def empty_collections_payloads() -> dict[str, dict]:
    return {
        "source/source-index.json": {"sources": []},
        "knowledge/facts.json": {"facts": []},
        "knowledge/claims.json": {"claims": []},
        "knowledge/decisions.json": {"decisions": []},
        "knowledge/constraints.json": {"constraints": []},
        "knowledge/glossary.json": {"terms": []},
        "evidence/evidence.json": {"evidence": []},
        "evidence/references.json": {"references": []},
        "uncertainty/unknowns.json": {"unknowns": []},
        "uncertainty/conflicts.json": {"conflicts": []},
        "handoff/questions.json": {"questions": []},
        "handoff/recommended-actions.json": {"actions": []},
    }


def build_valid_minimal_package(dest: Path, *, empty: bool = False) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "source/original").mkdir(parents=True, exist_ok=True)
    write(dest / "knowledge/overview.md", "# Overview\n\nMinimal.\n")
    write(dest / "handoff/receiver-guide.md", "# Receiver guide\n\nMinimal.\n")
    write(dest / "source/original/design.md", "line1\n生产环境服务默认监听 8080 端口。\n")

    if empty:
        dump_yaml(
            dest / "manifest.yaml",
            minimal_manifest(
                package_id="pkg_validator_empty",
                sources_summary={"count": 0, "source_ids": []},
            ),
        )
        for rel, obj in empty_collections_payloads().items():
            dump_json(dest / rel, obj)
        return dest

    dump_yaml(dest / "manifest.yaml", minimal_manifest())
    # Integrity-consistent minimal graph (schema fixtures alone are not link-complete).
    dump_json(
        dest / "source/source-index.json",
        {
            "sources": [
                {
                    "source_id": "src_001",
                    "original_name": "design.md",
                    "user_path": None,
                    "package_path": "source/original/design.md",
                    "media_type": "text/markdown",
                    "language": "zh",
                    "role": "primary",
                    "received_from": "user",
                    "content_transformed": None,
                    "readable": True,
                    "notes": "",
                }
            ]
        },
    )
    dump_json(
        dest / "knowledge/facts.json",
        {
            "facts": [
                {
                    "fact_id": "fact_001",
                    "statement": {"text": "生产环境服务默认监听 8080 端口。", "lang": "zh"},
                    "status": "verified",
                    "evidence_ids": ["ev_001"],
                    "confirmation": None,
                    "conflict_ids": [],
                    "notes": "",
                }
            ]
        },
    )
    for rel, key in [
        ("knowledge/claims.json", "claims"),
        ("knowledge/decisions.json", "decisions"),
        ("knowledge/constraints.json", "constraints"),
        ("knowledge/glossary.json", "terms"),
        ("evidence/references.json", "references"),
        ("uncertainty/unknowns.json", "unknowns"),
        ("uncertainty/conflicts.json", "conflicts"),
        ("handoff/questions.json", "questions"),
        ("handoff/recommended-actions.json", "actions"),
    ]:
        dump_json(dest / rel, {key: []})
    dump_json(
        dest / "evidence/evidence.json",
        {
            "evidence": [
                {
                    "evidence_id": "ev_001",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 2,
                        "end": 2,
                        "excerpt": "生产环境服务默认监听 8080 端口。",
                    },
                    "supports": [{"type": "fact", "id": "fact_001"}],
                    "redaction_applied": False,
                    "notes": "",
                }
            ]
        },
    )
    return dest


def result_map(report: dict) -> dict[str, dict]:
    return {c["id"]: c for c in report["checks"]}


def expect_status(report: dict, check_id: str, status: str, label: str) -> None:
    rm = result_map(report)
    if check_id not in rm:
        fail(label, f"{check_id} missing from report")
        return
    got = rm[check_id]["result"]
    check(label, got == status, f"{check_id} expected {status}, got {got}")


def test_generated_output() -> None:
    before = fingerprint_package(GENERATED)
    report = validate_package(GENERATED)
    after = fingerprint_package(GENERATED)
    check("generated-output read-only hash", before == after, "digests changed")
    check("generated-output no abs user path", "Users" not in json.dumps(report))
    check(
        "generated-output package_label privacy",
        report["package_label"] == "generated-output",
    )
    check("generated-output L1 not FAIL", report["layers"]["L1"] != "FAIL")
    check("generated-output L2 not FAIL", report["layers"]["L2"] != "FAIL")
    check(
        "generated-output final semantically_unreviewed",
        report["final_status"] == "semantically_unreviewed",
        report["final_status"],
    )
    check("generated-output L3 PASS", report["layers"]["L3"] == "PASS", report["layers"]["L3"])
    check("generated-output L4 NOT_CHECKED", report["layers"]["L4"] == "NOT_CHECKED")
    check("generated-output wrote_to_package false", report["wrote_to_package"] is False)
    rm = result_map(report)
    for iid in ["I01", "I02", "I03", "I04", "I09", "I15", "I18"]:
        if rm.get(iid, {}).get("result") != "PASS":
            fail("generated-output L3-A core", f"{iid}={rm.get(iid)}")
            break
    else:
        ok("generated-output L3-A core PASS")
    for iid in ["I10", "I11"]:
        if rm.get(iid, {}).get("result") != "PASS":
            fail("generated-output L3-B1", f"{iid}={rm.get(iid)}")
            break
    else:
        ok("generated-output L3-B1 I10/I11 PASS")
    if rm.get("I16", {}).get("result") == "PASS":
        ok("generated-output L3-B2 I16 PASS")
    else:
        fail("generated-output L3-B2 I16", str(rm.get("I16")))
    if rm.get("I12", {}).get("result") == "PASS":
        ok("generated-output L3-B3 I12 PASS")
    else:
        fail("generated-output L3-B3 I12", str(rm.get("I12")))
    if rm.get("I13", {}).get("result") == "PASS":
        ok("generated-output L3-B4 I13 PASS")
    else:
        fail("generated-output L3-B4 I13", str(rm.get("I13")))
    if rm.get("I14", {}).get("result") == "PASS":
        ok("generated-output L3-C1 I14 PASS")
    else:
        fail("generated-output L3-C1 I14", str(rm.get("I14")))
    if rm.get("I20", {}).get("result") == "PASS":
        ok("generated-output L3-C2 I20 PASS")
    else:
        fail("generated-output L3-C2 I20", str(rm.get("I20")))


def test_valid_minimal_and_empty() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        minimal = build_valid_minimal_package(root / "minimal")
        report = validate_package(minimal)
        check("minimal L1 PASS-ish", report["layers"]["L1"] in {"PASS", "WARNING"})
        check("minimal L2 PASS", report["layers"]["L2"] == "PASS")
        check("minimal final_status", report["final_status"] == "not_fully_validated")
        expect_status(report, "P01", "PASS", "minimal P01")
        expect_status(report, "P03", "PASS", "minimal P03")
        expect_status(report, "P04", "PASS", "minimal P04")
        expect_status(report, "S02", "PASS", "minimal S02")
        expect_status(report, "S15", "PASS", "minimal S15")

        empty = build_valid_minimal_package(root / "empty", empty=True)
        report_e = validate_package(empty)
        check("empty L2 PASS", report_e["layers"]["L2"] == "PASS", report_e["layers"]["L2"])
        expect_status(report_e, "S04", "PASS", "empty facts schema")
        expect_status(report_e, "S09", "PASS", "empty evidence schema")


def test_l1_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # missing required file
        pkg = build_valid_minimal_package(root / "missing_file")
        (pkg / "knowledge/facts.json").unlink()
        report = validate_package(pkg)
        expect_status(report, "P01", "FAIL", "missing file P01")
        expect_status(report, "S04", "NOT_CHECKED", "missing file → S04 NOT_CHECKED")
        check("missing file invalid", report["final_status"] == "invalid")

        # missing required directory
        pkg = build_valid_minimal_package(root / "missing_dir")
        shutil.rmtree(pkg / "source/original")
        report = validate_package(pkg)
        expect_status(report, "P01", "FAIL", "missing dir P01")

        # bad YAML syntax
        pkg = build_valid_minimal_package(root / "bad_yaml")
        write(pkg / "manifest.yaml", "cbhf_version: [\n  broken\n")
        report = validate_package(pkg)
        expect_status(report, "P04", "FAIL", "bad YAML P04")
        expect_status(report, "S02", "NOT_CHECKED", "bad YAML → S02 NOT_CHECKED")
        expect_status(report, "P05", "NOT_CHECKED", "bad YAML → P05 NOT_CHECKED")

        # YAML duplicate keys
        pkg = build_valid_minimal_package(root / "dup_yaml")
        write(
            pkg / "manifest.yaml",
            "cbhf_version: \"0.1.0\"\ncbhf_version: \"0.1.0\"\nprotocol: CBHF\n",
        )
        report = validate_package(pkg)
        expect_status(report, "P04", "FAIL", "dup YAML P04")

        # bad JSON syntax
        pkg = build_valid_minimal_package(root / "bad_json")
        write(pkg / "knowledge/facts.json", "{not-json")
        report = validate_package(pkg)
        expect_status(report, "P03", "FAIL", "bad JSON P03")
        expect_status(report, "S04", "NOT_CHECKED", "bad JSON → S04 NOT_CHECKED")

        # JSON duplicate keys
        pkg = build_valid_minimal_package(root / "dup_json")
        write(
            pkg / "knowledge/facts.json",
            '{\n  "facts": [],\n  "facts": []\n}\n',
        )
        report = validate_package(pkg)
        expect_status(report, "P03", "FAIL", "dup JSON P03")
        expect_status(report, "S04", "NOT_CHECKED", "dup JSON → S04 NOT_CHECKED")

        # extra top-level → WARNING (Q1)
        pkg = build_valid_minimal_package(root / "extra")
        write(pkg / "NOTES.txt", "extra\n")
        report = validate_package(pkg)
        expect_status(report, "P06", "WARNING", "extra file P06 WARNING")
        check(
            "extra file not upgraded to FAIL",
            result_map(report)["P06"]["result"] == "WARNING",
        )
        check(
            "extra file final not invalid",
            report["final_status"] != "invalid",
            report["final_status"],
        )


def test_l2_errors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # illegal enum on references
        pkg = build_valid_minimal_package(root / "illegal_enum")
        shutil.copy(
            FIXTURE_SCHEMA / "invalid/illegal_status_reference.json",
            pkg / "evidence/references.json",
        )
        report = validate_package(pkg)
        expect_status(report, "S10", "FAIL", "illegal enum S10")
        expect_status(report, "S15", "FAIL", "illegal enum S15")
        check("illegal enum invalid", report["final_status"] == "invalid")

        # missing required field (manifest)
        pkg = build_valid_minimal_package(root / "missing_required")
        bad = minimal_manifest()
        del bad["limitations"]
        dump_yaml(pkg / "manifest.yaml", bad)
        report = validate_package(pkg)
        expect_status(report, "P04", "PASS", "missing required still parses")
        expect_status(report, "S02", "FAIL", "missing required S02")

        # wrong field type
        pkg = build_valid_minimal_package(root / "wrong_type")
        shutil.copy(
            FIXTURE_SCHEMA / "invalid/wrong_type_content_transformed.json",
            pkg / "source/source-index.json",
        )
        report = validate_package(pkg)
        expect_status(report, "S03", "FAIL", "wrong type S03")

        # additionalProperties / verified without evidence
        pkg = build_valid_minimal_package(root / "verified_no_ev")
        shutil.copy(
            FIXTURE_SCHEMA / "invalid/verified_without_evidence.json",
            pkg / "knowledge/facts.json",
        )
        report = validate_package(pkg)
        expect_status(report, "S04", "FAIL", "verified without evidence S04")

        # extra field on facts document
        pkg = build_valid_minimal_package(root / "extra_field")
        dump_json(
            pkg / "knowledge/facts.json",
            {"facts": [], "not_allowed": True},
        )
        report = validate_package(pkg)
        expect_status(report, "S04", "FAIL", "additionalProperties S04")


def test_schema_load_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = build_valid_minimal_package(root / "pkg")
        empty_schemas = root / "schemas"
        empty_schemas.mkdir()
        report = validate_package(pkg, schema_dir=empty_schemas)
        expect_status(report, "S01", "FAIL", "schema load S01")
        expect_status(report, "S02", "NOT_CHECKED", "schema load → S02 NOT_CHECKED")
        expect_status(report, "S15", "NOT_CHECKED", "schema load → S15 NOT_CHECKED")
        check("schema load final invalid", report["final_status"] == "invalid")


def test_report_structure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "pkg")
        report = validate_package(pkg)
        required_keys = [
            "report_kind",
            "cbhf_version",
            "package_label",
            "validated_at",
            "checker",
            "layers",
            "checks",
            "final_status",
            "not_checked",
            "wrote_to_package",
            "limitations",
        ]
        for key in required_keys:
            check(f"report has {key}", key in report)
        check(
            "checker phase 3B-C2",
            report["checker"]["phase"] == "3B-C2",
        )
        check(
            "checker L3 integrity true",
            report["checker"]["scripts_implemented"]["L3_integrity"] is True,
        )
        check(
            "checker L3-A true",
            report["checker"]["scripts_implemented"]["L3_A_references"] is True,
        )
        check(
            "checker L3-B1 true",
            report["checker"]["scripts_implemented"]["L3_B1_path_safety_exists"] is True,
        )
        check(
            "checker L3-B2 true",
            report["checker"]["scripts_implemented"]["L3_B2_readable_false"] is True,
        )
        check(
            "checker L3-B3 true",
            report["checker"]["scripts_implemented"]["L3_B3_line_range_bounds"] is True,
        )
        check(
            "checker L3-B4 true",
            report["checker"]["scripts_implemented"]["L3_B4_other_locators"] is True,
        )
        check(
            "checker L3-C excerpts true",
            report["checker"]["scripts_implemented"]["L3_C_excerpts"] is True,
        )
        check(
            "checker L3-C checksum true",
            report["checker"]["scripts_implemented"]["L3_C_checksum"] is True,
        )
        check(
            "checker L4 semantic false",
            report["checker"]["scripts_implemented"]["L4_semantic"] is False,
        )
        check(
            "checker network false",
            report["checker"]["network"] is False,
        )
        ids = {c["id"] for c in report["checks"]}
        for pid in [f"P{i:02d}" for i in range(1, 8)]:
            check(f"report includes {pid}", pid in ids)
        for sid in [f"S{i:02d}" for i in range(1, 16)]:
            check(f"report includes {sid}", sid in ids)


def test_network_not_required() -> None:
    # Guard: validate_package module must not call urlopen during validation.
    import urllib.request

    calls: list[str] = []
    original = urllib.request.urlopen

    def blocked(*args, **kwargs):
        calls.append("urlopen")
        raise RuntimeError("network blocked in validator test")

    urllib.request.urlopen = blocked  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            pkg = build_valid_minimal_package(Path(tmp) / "pkg")
            report = validate_package(pkg)
            check("no urlopen during validate", calls == [])
            check("offline L2 still PASS", report["layers"]["L2"] == "PASS")
    finally:
        urllib.request.urlopen = original  # type: ignore[assignment]


def main() -> int:
    print("== context-validator Phase 2 L1+L2 tests ==")
    check("validate_package.py exists", SCRIPT.is_file())
    check("generated-output exists", GENERATED.is_dir())
    check("schema dir exists", SCHEMA_DIR.is_dir())

    test_generated_output()
    test_valid_minimal_and_empty()
    test_l1_errors()
    test_l2_errors()
    test_schema_load_failure()
    test_report_structure()
    test_network_not_required()

    print(f"\nSummary: {PASSES} passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
