#!/usr/bin/env python3
"""Phase 3B-1 tests for context-validator L3-A (reference integrity)."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills/context-validator/scripts/validate_package.py"
GENERATED = ROOT / "examples/technical-proposal/generated-output"

sys.path.insert(0, str(SCRIPT.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_package import fingerprint_package, validate_package  # noqa: E402
from run_l1_l2_tests import (  # noqa: E402
    build_valid_minimal_package,
    dump_json,
    result_map,
)

PASSES = 0
FAILURES: list[str] = []

L3A = ["I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08", "I09", "I15", "I17", "I18", "I19"]
L3_DEFERRED = ["I10", "I11", "I12", "I13", "I14", "I16", "I20"]


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


def expect_status(report: dict, check_id: str, status: str, label: str) -> None:
    rm = result_map(report)
    got = rm.get(check_id, {}).get("result")
    check(label, got == status, f"{check_id} expected {status}, got {got}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, obj) -> None:
    dump_json(path, obj)


def test_generated_temp_copy() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "generated-output"
        shutil.copytree(GENERATED, pkg)
        before = fingerprint_package(pkg)
        report = validate_package(pkg)
        after = fingerprint_package(pkg)
        check("generated copy read-only", before == after)
        check("generated copy final", report["final_status"] == "not_fully_validated")
        check(
            "generated copy L3 layer incomplete",
            report["layers"]["L3"] == "NOT_CHECKED",
            report["layers"]["L3"],
        )
        check("generated copy L4", report["layers"]["L4"] == "NOT_CHECKED")
        rm = result_map(report)
        for iid in ["I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08", "I09", "I15", "I17", "I18", "I19"]:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_DEFERRED:
            expect_status(report, iid, "NOT_CHECKED", f"generated deferred {iid}")
        for hid in [f"H{i:02d}" for i in range(1, 7)]:
            expect_status(report, hid, "NOT_CHECKED", f"generated {hid}")


def test_empty_and_minimal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        empty = build_valid_minimal_package(Path(tmp) / "empty", empty=True)
        report = validate_package(empty)
        for iid in L3A:
            if iid == "I19":
                expect_status(report, iid, "PASS", f"empty {iid}")
            else:
                expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_DEFERRED:
            expect_status(report, iid, "NOT_CHECKED", f"empty deferred {iid}")

        minimal = build_valid_minimal_package(Path(tmp) / "minimal")
        report_m = validate_package(minimal)
        expect_status(report_m, "I01", "PASS", "minimal I01")
        expect_status(report_m, "I02", "PASS", "minimal I02")
        expect_status(report_m, "I03", "PASS", "minimal I03")
        expect_status(report_m, "I04", "PASS", "minimal I04")
        expect_status(report_m, "I09", "PASS", "minimal I09")
        expect_status(report_m, "I15", "PASS", "minimal I15")
        check("minimal not invalid", report_m["final_status"] != "invalid")


def test_duplicate_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "dup")
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"].append(dict(facts["facts"][0]))  # same fact_id
        save_json(pkg / "knowledge/facts.json", facts)
        report = validate_package(pkg)
        expect_status(report, "I01", "FAIL", "dup I01")
        check("dup final invalid", report["final_status"] == "invalid")


def test_missing_supports_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "bad_sup")
        ev = load_json(pkg / "evidence/evidence.json")
        ev["evidence"][0]["supports"] = [{"type": "claim", "id": "claim_missing"}]
        save_json(pkg / "evidence/evidence.json", ev)
        # break reverse to isolate I02 (also breaks I04)
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"][0]["evidence_ids"] = []
        facts["facts"][0]["status"] = "unverified"
        save_json(pkg / "knowledge/facts.json", facts)
        report = validate_package(pkg)
        expect_status(report, "I02", "FAIL", "missing supports target I02")


def test_missing_evidence_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "bad_eid")
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"][0]["evidence_ids"] = ["ev_missing"]
        save_json(pkg / "knowledge/facts.json", facts)
        report = validate_package(pkg)
        expect_status(report, "I03", "FAIL", "missing evidence_ids I03")


def test_one_way_links() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        # knowledge lists evidence but evidence does not support back
        pkg = build_valid_minimal_package(Path(tmp) / "one_way_k")
        ev = load_json(pkg / "evidence/evidence.json")
        ev["evidence"][0]["supports"] = []
        save_json(pkg / "evidence/evidence.json", ev)
        report = validate_package(pkg)
        expect_status(report, "I04", "FAIL", "one-way knowledge→evidence I04")
        expect_status(report, "I19", "WARNING", "empty supports I19 WARNING")

        pkg2 = build_valid_minimal_package(Path(tmp) / "one_way_e")
        facts = load_json(pkg2 / "knowledge/facts.json")
        facts["facts"][0]["evidence_ids"] = []
        facts["facts"][0]["status"] = "unverified"
        save_json(pkg2 / "knowledge/facts.json", facts)
        report2 = validate_package(pkg2)
        expect_status(report2, "I04", "FAIL", "one-way evidence→knowledge I04")


def test_conflict_and_related() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "cfl")
        # add second fact + conflict with bad party
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"].append(
            {
                "fact_id": "fact_002",
                "statement": {"text": "alt", "lang": "en"},
                "status": "unverified",
                "evidence_ids": [],
                "confirmation": None,
                "conflict_ids": ["cfl_001"],
                "notes": "",
            }
        )
        save_json(pkg / "knowledge/facts.json", facts)
        save_json(
            pkg / "uncertainty/conflicts.json",
            {
                "conflicts": [
                    {
                        "conflict_id": "cfl_001",
                        "summary": {"text": "ports", "lang": "en"},
                        "same_subject": True,
                        "context_alignment": "same",
                        "parties": [
                            {"type": "fact", "id": "fact_001", "stance": "a"},
                            {"type": "fact", "id": "fact_missing", "stance": "b"},
                        ],
                        "evidence_ids": ["ev_missing"],
                        "resolution": None,
                        "notes": "",
                    }
                ]
            },
        )
        report = validate_package(pkg)
        expect_status(report, "I05", "FAIL", "bad party I05")
        expect_status(report, "I06", "FAIL", "bad conflict evidence I06")

        pkg2 = build_valid_minimal_package(Path(tmp) / "rel")
        save_json(
            pkg2 / "handoff/questions.json",
            {
                "questions": [
                    {
                        "question_id": "q_001",
                        "ask": {"text": "?", "lang": "en"},
                        "priority": "high",
                        "related_conflict_ids": ["cfl_missing"],
                        "related_unknown_ids": [],
                        "notes": "",
                    }
                ]
            },
        )
        report2 = validate_package(pkg2)
        expect_status(report2, "I07", "FAIL", "bad related_conflict I07")


def test_source_ref_and_locator_source() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "sref")
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"][0]["status"] = "user_confirmed"
        facts["facts"][0]["evidence_ids"] = []
        facts["facts"][0]["confirmation"] = {
            "confirmed_by": "user",
            "source_type": "user_authored_source",
            "source_ref": "src_missing",
            "confirmation_text": "yes",
            "confirmed_at": None,
            "limitations": None,
        }
        save_json(pkg / "knowledge/facts.json", facts)
        # clear evidence supports to avoid I04 noise from empty evidence_ids
        ev = load_json(pkg / "evidence/evidence.json")
        ev["evidence"][0]["supports"] = []
        save_json(pkg / "evidence/evidence.json", ev)
        report = validate_package(pkg)
        expect_status(report, "I08", "FAIL", "bad source_ref I08")

        pkg2 = build_valid_minimal_package(Path(tmp) / "lsrc")
        ev2 = load_json(pkg2 / "evidence/evidence.json")
        ev2["evidence"][0]["locator"]["source_id"] = "src_missing"
        save_json(pkg2 / "evidence/evidence.json", ev2)
        report2 = validate_package(pkg2)
        expect_status(report2, "I09", "FAIL", "bad locator.source_id I09")


def test_verified_and_i18() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg2 = build_valid_minimal_package(Path(tmp) / "val")
        manifest = (pkg2 / "manifest.yaml").read_text(encoding="utf-8")
        manifest = manifest.replace("present: false", "present: true")
        (pkg2 / "manifest.yaml").write_text(manifest, encoding="utf-8")
        report2 = validate_package(pkg2)
        expect_status(report2, "I18", "FAIL", "present true without report I18")


def test_optional_fields_and_dependency() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        # optional related_* absent / empty → PASS
        pkg = build_valid_minimal_package(Path(tmp) / "opt")
        report = validate_package(pkg)
        expect_status(report, "I07", "PASS", "optional related empty I07")
        expect_status(report, "I08", "PASS", "no user_authored confirmations I08")

        # missing evidence file → dependency NOT_CHECKED
        pkg2 = build_valid_minimal_package(Path(tmp) / "dep")
        (pkg2 / "evidence/evidence.json").unlink()
        report2 = validate_package(pkg2)
        expect_status(report2, "P01", "FAIL", "dep missing file P01")
        expect_status(report2, "I02", "NOT_CHECKED", "dep I02 NOT_CHECKED")
        expect_status(report2, "I03", "NOT_CHECKED", "dep I03 NOT_CHECKED")
        expect_status(report2, "I04", "NOT_CHECKED", "dep I04 NOT_CHECKED")
        expect_status(report2, "I09", "NOT_CHECKED", "dep I09 NOT_CHECKED")


def test_cross_kind_same_string_ok() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "cross")
        claims = {
            "claims": [
                {
                    "claim_id": "fact_001",  # same string as fact_id, different kind
                    "statement": {"text": "x", "lang": "en"},
                    "status": "unverified",
                    "kind": "assertion",
                    "evidence_ids": [],
                    "confirmation": None,
                    "conflict_ids": [],
                    "notes": "",
                }
            ]
        }
        save_json(pkg / "knowledge/claims.json", claims)
        report = validate_package(pkg)
        expect_status(report, "I01", "PASS", "cross-kind same string I01 PASS")


def test_review_fix_i01_partial() -> None:
    """Schema-failed collection must not yield I01 PASS."""
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "i01_partial")
        facts = load_json(pkg / "knowledge/facts.json")
        facts["not_allowed"] = True  # additionalProperties → S04 FAIL
        save_json(pkg / "knowledge/facts.json", facts)
        report = validate_package(pkg)
        expect_status(report, "S04", "FAIL", "partial S04 FAIL")
        expect_status(report, "I01", "NOT_CHECKED", "partial I01 NOT_CHECKED")


def test_review_fix_i07_incomplete_vs_complete() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        # Target conflict collection schema-failed → typed related must NOT_CHECKED
        pkg = build_valid_minimal_package(Path(tmp) / "i07_inc")
        save_json(
            pkg / "uncertainty/conflicts.json",
            {"conflicts": [], "extra_forbidden": True},
        )
        save_json(
            pkg / "handoff/questions.json",
            {
                "questions": [
                    {
                        "question_id": "q_001",
                        "ask": {"text": "?", "lang": "en"},
                        "priority": "high",
                        "related_conflict_ids": ["cfl_x"],
                        "related_unknown_ids": [],
                        "notes": "",
                    }
                ]
            },
        )
        report = validate_package(pkg)
        expect_status(report, "S12", "FAIL", "i07 incomplete S12 FAIL")
        expect_status(report, "I07", "NOT_CHECKED", "i07 target unloaded NOT_CHECKED")

        # All collections loaded; untyped related_ids truly missing → FAIL
        pkg2 = build_valid_minimal_package(Path(tmp) / "i07_full")
        save_json(
            pkg2 / "handoff/recommended-actions.json",
            {
                "actions": [
                    {
                        "action_id": "act_001",
                        "action": {"text": "do", "lang": "en"},
                        "priority": "high",
                        "status": "pending",
                        "related_ids": ["id_does_not_exist_anywhere"],
                        "notes": "",
                    }
                ]
            },
        )
        report2 = validate_package(pkg2)
        expect_status(report2, "I07", "FAIL", "i07 complete unknown related FAIL")
        base = build_valid_minimal_package(Path(tmp) / "i07_base")
        base_msg = result_map(validate_package(base))["I07"]["message"]
        check(
            "i07 complete index flag on clean package",
            "all_ids_complete=true" in base_msg,
            base_msg,
        )


def test_review_fix_i15_independent() -> None:
    """I15 must FAIL on its own when knowledge is indexed with verified+empty evidence_ids."""
    from _integrity import PackageIndex, check_i15

    idx = PackageIndex()
    for kind in ("fact", "claim", "decision", "constraint", "term"):
        idx.loaded_kinds.add(kind)
        idx.by_kind[kind] = {}
    idx.by_kind["fact"] = {
        "fact_001": {
            "fact_id": "fact_001",
            "status": "verified",
            "evidence_ids": [],
        }
    }
    out = check_i15(idx)
    check("I15 independent FAIL", out.result == "FAIL", out.message)


def test_review_fix_i17_branches() -> None:
    from _integrity import check_i17

    out_fail = check_i17({"S03": "FAIL"})
    check("I17 S03 FAIL → NOT_CHECKED", out_fail.result == "NOT_CHECKED")
    out_nc = check_i17({"S03": "NOT_CHECKED"})
    check("I17 S03 NOT_CHECKED", out_nc.result == "NOT_CHECKED")
    out_pass = check_i17({"S03": "PASS"})
    check("I17 S03 PASS", out_pass.result == "PASS")


def test_review_fix_i18_paths() -> None:
    import yaml
    from _integrity import classify_package_rel_file

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def write_manifest(pkg: Path, present: bool, report_path):
            data = yaml.safe_load((pkg / "manifest.yaml").read_text(encoding="utf-8"))
            data["validation"] = {"present": present, "report_path": report_path}
            (pkg / "manifest.yaml").write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

        # Specified report_path missing; default path exists must NOT mask
        pkg = build_valid_minimal_package(root / "i18_mask")
        (pkg / "validation").mkdir()
        (pkg / "validation/validation-report.json").write_text("{}\n", encoding="utf-8")
        write_manifest(pkg, True, "validation/custom-report.json")
        report = validate_package(pkg)
        expect_status(report, "I18", "FAIL", "I18 specified missing despite default")

        # Absolute path
        pkg2 = build_valid_minimal_package(root / "i18_abs")
        write_manifest(pkg2, True, str((root / "outside.json").resolve()))
        report2 = validate_package(pkg2)
        expect_status(report2, "I18", "FAIL", "I18 absolute path FAIL")

        # .. escape
        pkg3 = build_valid_minimal_package(root / "i18_dotdot")
        write_manifest(pkg3, True, "../outside-report.json")
        report3 = validate_package(pkg3)
        expect_status(report3, "I18", "FAIL", "I18 .. escape FAIL")

        # Symlink to outside
        pkg4 = build_valid_minimal_package(root / "i18_link")
        outside = root / "secret-report.json"
        outside.write_text("{}\n", encoding="utf-8")
        (pkg4 / "validation").mkdir()
        link = pkg4 / "validation" / "validation-report.json"
        try:
            link.symlink_to(outside)
            write_manifest(pkg4, True, None)
            report4 = validate_package(pkg4)
            expect_status(report4, "I18", "FAIL", "I18 symlink escape FAIL")
            code, _ = classify_package_rel_file(pkg4, "validation/validation-report.json")
            check("I18 symlink classify unsafe", code == "unsafe", code)
        except OSError:
            # Host cannot create symlinks; still verify classifier rejects absolute.
            code, _ = classify_package_rel_file(pkg4, str(outside))
            check("I18 symlink skipped; absolute still unsafe", code == "unsafe", code)

        # S02 dependency: break manifest schema
        pkg5 = build_valid_minimal_package(root / "i18_s02")
        data = yaml.safe_load((pkg5 / "manifest.yaml").read_text(encoding="utf-8"))
        del data["limitations"]
        data["validation"] = {"present": True, "report_path": None}
        (pkg5 / "manifest.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        report5 = validate_package(pkg5)
        expect_status(report5, "S02", "FAIL", "I18 dep S02 FAIL")
        expect_status(report5, "I18", "NOT_CHECKED", "I18 depends S02 NOT_CHECKED")


def test_review_fix_l3_layer_mixed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "layer")
        report = validate_package(pkg)
        check(
            "L3 layer not full PASS with deferred I*",
            report["layers"]["L3"] == "NOT_CHECKED",
            report["layers"]["L3"],
        )
        check("L1 unchanged style", report["layers"]["L1"] in {"PASS", "WARNING"})
        check("L2 PASS", report["layers"]["L2"] == "PASS")
        # Per-check deferred still NOT_CHECKED; A rules still individual PASS
        expect_status(report, "I01", "PASS", "layer mix I01 PASS")
        expect_status(report, "I14", "NOT_CHECKED", "layer mix I14 NOT_CHECKED")


def test_report_and_offline() -> None:
    import urllib.request

    calls: list[str] = []
    original = urllib.request.urlopen

    def blocked(*args, **kwargs):
        calls.append("urlopen")
        raise RuntimeError("blocked")

    urllib.request.urlopen = blocked  # type: ignore[assignment]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            pkg = build_valid_minimal_package(Path(tmp) / "pkg")
            report = validate_package(pkg)
            check("no network", calls == [])
            check("phase 3B-1", report["checker"]["phase"] == "3B-1")
            check("L3-A flag", report["checker"]["scripts_implemented"]["L3_A_references"] is True)
            check("L3-B false", report["checker"]["scripts_implemented"]["L3_B_locators"] is False)
            check("read_only", report["read_only"] is True)
            ids = {c["id"] for c in report["checks"]}
            for iid in L3A + L3_DEFERRED:
                check(f"report has {iid}", iid in ids)
    finally:
        urllib.request.urlopen = original  # type: ignore[assignment]


def main() -> int:
    print("== context-validator Phase 3B-1 L3-A tests ==")
    check("script exists", SCRIPT.is_file())
    check("generated-output exists", GENERATED.is_dir())

    test_generated_temp_copy()
    test_empty_and_minimal()
    test_duplicate_id()
    test_missing_supports_target()
    test_missing_evidence_id()
    test_one_way_links()
    test_conflict_and_related()
    test_source_ref_and_locator_source()
    test_verified_and_i18()
    test_optional_fields_and_dependency()
    test_cross_kind_same_string_ok()
    test_review_fix_i01_partial()
    test_review_fix_i07_incomplete_vs_complete()
    test_review_fix_i15_independent()
    test_review_fix_i17_branches()
    test_review_fix_i18_paths()
    test_review_fix_l3_layer_mixed()
    test_report_and_offline()

    print(f"\nSummary: {PASSES} passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
