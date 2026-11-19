#!/usr/bin/env python3
"""Tests for context-validator L3-A + L3-B1/B2/B3/B4 + L3-C1 (I14) + L3-C2 (I20)."""

from __future__ import annotations

import hashlib
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
L3_B1 = ["I10", "I11"]
L3_B2 = ["I16"]
L3_B3 = ["I12"]
L3_B4 = ["I13"]
L3_C1 = ["I14"]
L3_C2 = ["I20"]
L3_DEFERRED: list[str] = []


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
        # All I* PASS (incl. I20) → L3 PASS; L4 unfinished → semantically_unreviewed
        check(
            "generated copy final",
            report["final_status"] == "semantically_unreviewed",
            report["final_status"],
        )
        check(
            "generated copy L3 layer PASS",
            report["layers"]["L3"] == "PASS",
            report["layers"]["L3"],
        )
        check("generated copy L4", report["layers"]["L4"] == "NOT_CHECKED")
        for iid in ["I01", "I02", "I03", "I04", "I05", "I06", "I07", "I08", "I09", "I15", "I17", "I18", "I19"]:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_B1:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_B2:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_B3:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_B4:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_C1:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_C2:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for hid in [f"H{i:02d}" for i in range(1, 7)]:
            expect_status(report, hid, "NOT_CHECKED", f"generated {hid}")


def test_empty_and_minimal() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        empty = build_valid_minimal_package(Path(tmp) / "empty", empty=True)
        report = validate_package(empty)
        for iid in L3A:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B1:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B2:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B3:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B4:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_C1:
            expect_status(report, iid, "PASS", f"empty {iid}")
        # Empty sources → zero applicable checksums → I20 NOT_CHECKED
        expect_status(report, "I20", "NOT_CHECKED", "empty I20 zero applicable")

        minimal = build_valid_minimal_package(Path(tmp) / "minimal")
        report_m = validate_package(minimal)
        expect_status(report_m, "I01", "PASS", "minimal I01")
        expect_status(report_m, "I14", "PASS", "minimal I14")
        expect_status(report_m, "I02", "PASS", "minimal I02")
        expect_status(report_m, "I03", "PASS", "minimal I03")
        expect_status(report_m, "I04", "PASS", "minimal I04")
        expect_status(report_m, "I09", "PASS", "minimal I09")
        # Minimal has source but no checksum → zero applicable → I20 NOT_CHECKED
        expect_status(report_m, "I20", "NOT_CHECKED", "minimal I20 zero applicable")
        expect_status(report_m, "I10", "PASS", "minimal I10")
        expect_status(report_m, "I11", "PASS", "minimal I11")
        expect_status(report_m, "I12", "PASS", "minimal I12")
        expect_status(report_m, "I13", "PASS", "minimal I13")
        expect_status(report_m, "I15", "PASS", "minimal I15")
        expect_status(report_m, "I16", "PASS", "minimal I16")
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
            "L3 layer not full PASS with zero-applicable I20",
            report["layers"]["L3"] == "NOT_CHECKED",
            report["layers"]["L3"],
        )
        check("L1 unchanged style", report["layers"]["L1"] in {"PASS", "WARNING"})
        check("L2 PASS", report["layers"]["L2"] == "PASS")
        expect_status(report, "I01", "PASS", "layer mix I01 PASS")
        expect_status(report, "I14", "PASS", "layer mix I14 PASS")
        expect_status(report, "I20", "NOT_CHECKED", "layer mix I20 zero applicable")


def test_convergence_i18_privacy_and_whitespace() -> None:
    import yaml

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def write_manifest(pkg: Path, present: bool, report_path):
            data = yaml.safe_load((pkg / "manifest.yaml").read_text(encoding="utf-8"))
            data["validation"] = {"present": present, "report_path": report_path}
            (pkg / "manifest.yaml").write_text(
                yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

        # Whitespace-padded path must strip and still locate / fail safely
        pkg = build_valid_minimal_package(root / "ws")
        (pkg / "validation").mkdir()
        (pkg / "validation/custom-report.json").write_text("{}\n", encoding="utf-8")
        write_manifest(pkg, True, "  validation/custom-report.json  ")
        report = validate_package(pkg)
        expect_status(report, "I18", "PASS", "I18 whitespace strip PASS")

        pkg2 = build_valid_minimal_package(root / "ws_miss")
        write_manifest(pkg2, True, "  validation/nope.json  ")
        report2 = validate_package(pkg2)
        expect_status(report2, "I18", "FAIL", "I18 whitespace strip missing FAIL")
        blob = json.dumps(report2)
        check("I18 no Users abs path in report", "Users" not in blob)
        check(
            "I18 reason code not raw exc",
            "report_file_missing" in blob or "forbidden_path_form" in blob,
        )

        # Absolute escape messages must not embed host paths from exceptions
        pkg3 = build_valid_minimal_package(root / "abs_priv")
        abs_target = str((root / "outside.json").resolve())
        write_manifest(pkg3, True, abs_target)
        report3 = validate_package(pkg3)
        expect_status(report3, "I18", "FAIL", "I18 abs privacy FAIL")
        i18 = result_map(report3)["I18"]
        check(
            "I18 message uses reason code",
            "forbidden_path_form" in i18["message"]
            or "path_escapes_or_unresolvable" in i18["message"],
            i18["message"],
        )
        check(
            "I18 message omits resolved abs target",
            abs_target not in i18["message"],
            i18["message"],
        )


def test_convergence_i01_partial_with_duplicate() -> None:
    """Duplicate in a loaded collection FAILs even when another collection is missing."""
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "i01_dup_partial")
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"].append(dict(facts["facts"][0]))
        facts["not_allowed"] = True  # would fail schema, but facts still parse
        # Break claims schema so claim kind is unloaded; facts remain loaded with dup
        save_json(pkg / "knowledge/facts.json", {"facts": facts["facts"]})
        save_json(
            pkg / "knowledge/claims.json",
            {"claims": [], "extra_forbidden": True},
        )
        report = validate_package(pkg)
        expect_status(report, "S05", "FAIL", "partial claims schema FAIL")
        expect_status(report, "I01", "FAIL", "partial+duplicate I01 FAIL")


def test_convergence_mid_dir_symlink() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pkg = build_valid_minimal_package(root / "midlink")
        outside_dir = root / "outside_dir"
        outside_dir.mkdir()
        (outside_dir / "validation-report.json").write_text("{}\n", encoding="utf-8")
        import yaml

        data = yaml.safe_load((pkg / "manifest.yaml").read_text(encoding="utf-8"))
        data["validation"] = {"present": True, "report_path": None}
        (pkg / "manifest.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        link = pkg / "validation"
        try:
            link.symlink_to(outside_dir, target_is_directory=True)
            report = validate_package(pkg)
            expect_status(report, "I18", "FAIL", "I18 mid-dir symlink FAIL")
            blob = json.dumps(report)
            check(
                "mid-dir symlink reason code",
                "path_escapes_or_unresolvable" in blob
                or "forbidden_path_form" in blob,
            )
            check("mid-dir symlink no abs leak", str(outside_dir.resolve()) not in blob)
        except OSError:
            from _integrity import classify_package_rel_file

            # Host cannot create dir symlinks; still assert classifier contracts.
            code, reason = classify_package_rel_file(pkg, "../outside_dir/x.json")
            check("mid-dir symlink skipped; .. unsafe", code == "unsafe", reason)


def test_convergence_l3_warning_vs_not_checked() -> None:
    """I19 WARNING must not make L3 layer look finished while I20 is NOT_CHECKED."""
    with tempfile.TemporaryDirectory() as tmp:
        pkg = build_valid_minimal_package(Path(tmp) / "warn_layer")
        ev = load_json(pkg / "evidence/evidence.json")
        ev["evidence"][0]["supports"] = []
        save_json(pkg / "evidence/evidence.json", ev)
        facts = load_json(pkg / "knowledge/facts.json")
        facts["facts"][0]["evidence_ids"] = []
        facts["facts"][0]["status"] = "unverified"
        save_json(pkg / "knowledge/facts.json", facts)
        report = validate_package(pkg)
        expect_status(report, "I19", "WARNING", "warn-layer I19 WARNING")
        expect_status(report, "I14", "PASS", "warn-layer I14 PASS")
        expect_status(report, "I20", "NOT_CHECKED", "warn-layer I20 zero applicable")
        check(
            "L3 layer NOT_CHECKED despite I19 WARNING",
            report["layers"]["L3"] == "NOT_CHECKED",
            report["layers"]["L3"],
        )
        check(
            "I19 still listed in warnings",
            any(w["id"] == "I19" for w in report["warnings"]),
        )
        check(
            "final_status still not_fully_validated",
            report["final_status"] == "not_fully_validated",
        )
        check("L1 still PASS-ish", report["layers"]["L1"] in {"PASS", "WARNING"})
        check("L2 still PASS", report["layers"]["L2"] == "PASS")


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
            check("phase 3B-C2", report["checker"]["phase"] == "3B-C2")
            check("L3-A flag", report["checker"]["scripts_implemented"]["L3_A_references"] is True)
            check(
                "L3-B1 flag",
                report["checker"]["scripts_implemented"]["L3_B1_path_safety_exists"] is True,
            )
            check(
                "L3-B2 flag",
                report["checker"]["scripts_implemented"]["L3_B2_readable_false"] is True,
            )
            check(
                "L3-B3 flag",
                report["checker"]["scripts_implemented"]["L3_B3_line_range_bounds"] is True,
            )
            check(
                "L3-B4 flag",
                report["checker"]["scripts_implemented"]["L3_B4_other_locators"] is True,
            )
            check(
                "L3-C excerpts flag",
                report["checker"]["scripts_implemented"]["L3_C_excerpts"] is True,
            )
            check(
                "L3-C checksum flag",
                report["checker"]["scripts_implemented"]["L3_C_checksum"] is True,
            )
            check(
                "L3 integrity flag",
                report["checker"]["scripts_implemented"]["L3_integrity"] is True,
            )
            check("L3-B full locators false", report["checker"]["scripts_implemented"]["L3_B_locators"] is False)
            check("L4 semantic false", report["checker"]["scripts_implemented"]["L4_semantic"] is False)
            check("read_only", report["read_only"] is True)
            ids = {c["id"] for c in report["checks"]}
            for iid in L3A + L3_B1 + L3_B2 + L3_B3 + L3_B4 + L3_C1 + L3_C2:
                check(f"report has {iid}", iid in ids)
    finally:
        urllib.request.urlopen = original  # type: ignore[assignment]


def _set_evidence_path(pkg: Path, new_path: str) -> None:
    ev = load_json(pkg / "evidence/evidence.json")
    ev["evidence"][0]["locator"]["path"] = new_path
    save_json(pkg / "evidence/evidence.json", ev)


def test_b1_i11_i10_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1) Normal in-package path
        pkg = build_valid_minimal_package(root / "ok")
        report = validate_package(pkg)
        expect_status(report, "I11", "PASS", "B1 normal I11")
        expect_status(report, "I10", "PASS", "B1 normal I10")

        # 2) Missing file (safe relative path)
        pkg2 = build_valid_minimal_package(root / "missing")
        _set_evidence_path(pkg2, "source/original/does-not-exist.md")
        report2 = validate_package(pkg2)
        expect_status(report2, "I11", "PASS", "B1 missing I11 PASS")
        expect_status(report2, "I10", "FAIL", "B1 missing I10 FAIL")

        # 3) Empty path
        pkg3 = build_valid_minimal_package(root / "empty_path")
        _set_evidence_path(pkg3, "")
        report3 = validate_package(pkg3)
        expect_status(report3, "I11", "FAIL", "B1 empty path I11 FAIL")
        expect_status(report3, "I10", "NOT_CHECKED", "B1 empty path I10 NOT_CHECKED")

        # 4) ../ traversal
        pkg4 = build_valid_minimal_package(root / "dotdot")
        outside = root / "outside_secret.txt"
        outside.write_text("SECRET_SHOULD_NOT_BE_READ\n", encoding="utf-8")
        _set_evidence_path(pkg4, "../outside_secret.txt")
        before = outside.read_text(encoding="utf-8")
        report4 = validate_package(pkg4)
        after = outside.read_text(encoding="utf-8")
        expect_status(report4, "I11", "FAIL", "B1 .. I11 FAIL")
        expect_status(report4, "I10", "NOT_CHECKED", "B1 .. I10 NOT_CHECKED")
        check("B1 .. did not alter outside file", before == after)
        blob4 = json.dumps(report4)
        check("B1 .. no abs leak", str(outside.resolve()) not in blob4)
        check("B1 .. reason code", "forbidden_path_form" in blob4)

        # 5) Absolute path
        pkg5 = build_valid_minimal_package(root / "abs")
        abs_p = str((root / "abs_target.md").resolve())
        (root / "abs_target.md").write_text("x\n", encoding="utf-8")
        _set_evidence_path(pkg5, abs_p)
        report5 = validate_package(pkg5)
        expect_status(report5, "I11", "FAIL", "B1 abs I11 FAIL")
        expect_status(report5, "I10", "NOT_CHECKED", "B1 abs I10 NOT_CHECKED")
        check("B1 abs not echoed", abs_p not in result_map(report5)["I11"]["message"])

        # 6) Windows drive
        pkg6 = build_valid_minimal_package(root / "drive")
        _set_evidence_path(pkg6, "C:\\Windows\\notepad.exe")
        report6 = validate_package(pkg6)
        expect_status(report6, "I11", "FAIL", "B1 drive I11 FAIL")
        expect_status(report6, "I10", "NOT_CHECKED", "B1 drive I10 NOT_CHECKED")

        # 7) UNC
        pkg7 = build_valid_minimal_package(root / "unc")
        _set_evidence_path(pkg7, "\\\\server\\share\\file.md")
        report7 = validate_package(pkg7)
        expect_status(report7, "I11", "FAIL", "B1 UNC I11 FAIL")
        expect_status(report7, "I10", "NOT_CHECKED", "B1 UNC I10 NOT_CHECKED")

        # 8) File symlink escape
        pkg8 = build_valid_minimal_package(root / "flink")
        target = root / "secret_file.md"
        target.write_text("SECRET\n", encoding="utf-8")
        link = pkg8 / "source/original/escape.md"
        try:
            if link.exists():
                link.unlink()
            link.symlink_to(target)
            _set_evidence_path(pkg8, "source/original/escape.md")
            report8 = validate_package(pkg8)
            expect_status(report8, "I11", "FAIL", "B1 file symlink I11 FAIL")
            expect_status(report8, "I10", "NOT_CHECKED", "B1 file symlink I10 NOT_CHECKED")
            check(
                "B1 file symlink no abs leak",
                str(target.resolve()) not in json.dumps(report8),
            )
        except OSError:
            from _integrity import classify_locator_path_safety

            st, reason = classify_locator_path_safety(pkg8, "../secret_file.md")
            check(
                "B1 file symlink skipped; .. unsafe",
                st == "unsafe",
                reason,
            )

        # 9) Mid-dir symlink escape
        pkg9 = build_valid_minimal_package(root / "dlink")
        outside_dir = root / "out_dir"
        outside_dir.mkdir()
        (outside_dir / "nested.md").write_text("SECRET\n", encoding="utf-8")
        link_dir = pkg9 / "source/escaped"
        try:
            link_dir.symlink_to(outside_dir, target_is_directory=True)
            _set_evidence_path(pkg9, "source/escaped/nested.md")
            report9 = validate_package(pkg9)
            expect_status(report9, "I11", "FAIL", "B1 mid-dir symlink I11 FAIL")
            expect_status(report9, "I10", "NOT_CHECKED", "B1 mid-dir symlink I10 NOT_CHECKED")
            check(
                "B1 mid-dir no abs leak",
                str(outside_dir.resolve()) not in json.dumps(report9),
            )
        except OSError:
            from _integrity import classify_locator_path_safety

            st, reason = classify_locator_path_safety(pkg9, "../out_dir/nested.md")
            check("B1 mid-dir symlink skipped; .. unsafe", st == "unsafe", reason)

        # 10) Empty evidence already covered in empty package — assert again
        empty = build_valid_minimal_package(root / "empty_ev", empty=True)
        report_e = validate_package(empty)
        expect_status(report_e, "I11", "PASS", "B1 empty evidence I11")
        expect_status(report_e, "I10", "PASS", "B1 empty evidence I10")


def _set_source_readable(pkg: Path, source_id: str, readable: bool) -> None:
    src = load_json(pkg / "source/source-index.json")
    for item in src["sources"]:
        if item["source_id"] == source_id:
            item["readable"] = readable
            break
    save_json(pkg / "source/source-index.json", src)


def _set_excerpt(pkg: Path, evidence_id: str, excerpt: str) -> None:
    ev = load_json(pkg / "evidence/evidence.json")
    for item in ev["evidence"]:
        if item["evidence_id"] == evidence_id:
            item["locator"]["excerpt"] = excerpt
            break
    save_json(pkg / "evidence/evidence.json", ev)


def _set_fact_status(pkg: Path, fact_id: str, status: str) -> None:
    facts = load_json(pkg / "knowledge/facts.json")
    for item in facts["facts"]:
        if item["fact_id"] == fact_id:
            item["status"] = status
            break
    save_json(pkg / "knowledge/facts.json", facts)


def test_b2_i16_readable_false() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1) readable:true + non-empty excerpt → PASS
        pkg = build_valid_minimal_package(root / "rtrue")
        report = validate_package(pkg)
        expect_status(report, "I16", "PASS", "B2 readable:true + excerpt I16 PASS")

        # 2) readable:false + non-empty excerpt → FAIL (Evidence)
        pkg2 = build_valid_minimal_package(root / "rfalse_excerpt")
        _set_source_readable(pkg2, "src_001", False)
        # keep verified → both Evidence + Knowledge FAIL
        report2 = validate_package(pkg2)
        expect_status(report2, "I16", "FAIL", "B2 readable:false + excerpt I16 FAIL")
        blob2 = json.dumps(report2)
        check("B2 reason readable_false_excerpt", "readable_false_excerpt" in blob2)
        check("B2 reason readable_false_verified", "readable_false_verified" in blob2)
        check("B2 no abs path leak", "Users" not in blob2)

        # 3) readable:false + empty excerpt, non-verified → PASS (no Evidence FAIL, no Knowledge FAIL)
        pkg3 = build_valid_minimal_package(root / "rfalse_empty")
        _set_source_readable(pkg3, "src_001", False)
        _set_excerpt(pkg3, "ev_001", "")
        _set_fact_status(pkg3, "fact_001", "unverified")
        report3 = validate_package(pkg3)
        expect_status(report3, "I16", "PASS", "B2 readable:false + empty excerpt non-verified PASS")

        # 4) readable:false + whitespace-only excerpt, non-verified → PASS
        pkg4 = build_valid_minimal_package(root / "rfalse_ws")
        _set_source_readable(pkg4, "src_001", False)
        _set_excerpt(pkg4, "ev_001", "   \t  ")
        _set_fact_status(pkg4, "fact_001", "unverified")
        report4 = validate_package(pkg4)
        expect_status(report4, "I16", "PASS", "B2 readable:false + whitespace excerpt PASS")

        # 5) readable:false + empty excerpt + verified → FAIL (Knowledge only)
        pkg5 = build_valid_minimal_package(root / "rfalse_empty_ver")
        _set_source_readable(pkg5, "src_001", False)
        _set_excerpt(pkg5, "ev_001", "")
        report5 = validate_package(pkg5)
        expect_status(report5, "I16", "FAIL", "B2 empty excerpt + verified FAIL")
        blob5 = json.dumps(result_map(report5)["I16"])
        check("B2 empty+verified has verified reason", "readable_false_verified" in blob5)
        check("B2 empty+verified no excerpt reason", "readable_false_excerpt" not in blob5)

        # 6) readable:false + non-empty + verified already covered in #2

        # 7) readable:false + non-verified + non-empty excerpt → FAIL (Evidence only)
        pkg7 = build_valid_minimal_package(root / "rfalse_nonver")
        _set_source_readable(pkg7, "src_001", False)
        _set_fact_status(pkg7, "fact_001", "unverified")
        report7 = validate_package(pkg7)
        expect_status(report7, "I16", "FAIL", "B2 readable:false + non-verified + excerpt FAIL")
        blob7 = json.dumps(result_map(report7)["I16"])
        check("B2 nonver excerpt reason", "readable_false_excerpt" in blob7)
        check("B2 nonver no verified reason", "readable_false_verified" not in blob7)

        # 8) Mixed sources: one readable true, one false; evidence quotes false → FAIL
        pkg8 = build_valid_minimal_package(root / "mixed_src")
        (pkg8 / "source/original/opaque.bin").write_bytes(b"\x00\x01")
        src = load_json(pkg8 / "source/source-index.json")
        src["sources"].append(
            {
                "source_id": "src_opaque",
                "original_name": "opaque.bin",
                "user_path": None,
                "package_path": "source/original/opaque.bin",
                "media_type": "application/octet-stream",
                "language": "und",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": False,
                "readable": False,
                "notes": "",
            }
        )
        save_json(pkg8 / "source/source-index.json", src)
        ev = load_json(pkg8 / "evidence/evidence.json")
        # keep ev_001 on readable true; add second evidence on opaque with excerpt
        ev["evidence"].append(
            {
                "evidence_id": "ev_opaque",
                "kind": "excerpt",
                "locator": {
                    "source_id": "src_opaque",
                    "path": "source/original/opaque.bin",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "fake quote from binary",
                },
                "supports": [],
                "redaction_applied": False,
                "notes": "",
            }
        )
        save_json(pkg8 / "evidence/evidence.json", ev)
        report8 = validate_package(pkg8)
        expect_status(report8, "I16", "FAIL", "B2 mixed sources opaque excerpt FAIL")
        check("B2 mixed keeps I09 PASS", result_map(report8)["I09"]["result"] == "PASS")

        # 9) verified depends on multiple evidence; only one readable:false → FAIL
        pkg9 = build_valid_minimal_package(root / "multi_ev")
        (pkg9 / "source/original/opaque.bin").write_bytes(b"\x00")
        src9 = load_json(pkg9 / "source/source-index.json")
        src9["sources"].append(
            {
                "source_id": "src_opaque",
                "original_name": "opaque.bin",
                "user_path": None,
                "package_path": "source/original/opaque.bin",
                "media_type": "application/octet-stream",
                "language": "und",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": False,
                "readable": False,
                "notes": "",
            }
        )
        save_json(pkg9 / "source/source-index.json", src9)
        ev9 = load_json(pkg9 / "evidence/evidence.json")
        # empty excerpt on opaque — Evidence clause does not FAIL; Knowledge does
        ev9["evidence"].append(
            {
                "evidence_id": "ev_opaque",
                "kind": "excerpt",
                "locator": {
                    "source_id": "src_opaque",
                    "path": "source/original/opaque.bin",
                    "locator_type": "line_range",
                    "start": None,
                    "end": None,
                    "excerpt": "",
                },
                "supports": [{"type": "fact", "id": "fact_001"}],
                "redaction_applied": False,
                "notes": "",
            }
        )
        save_json(pkg9 / "evidence/evidence.json", ev9)
        facts9 = load_json(pkg9 / "knowledge/facts.json")
        facts9["facts"][0]["evidence_ids"] = ["ev_001", "ev_opaque"]
        save_json(pkg9 / "knowledge/facts.json", facts9)
        report9 = validate_package(pkg9)
        expect_status(report9, "I16", "FAIL", "B2 multi-evidence one unreadable FAIL")
        blob9 = json.dumps(result_map(report9)["I16"])
        check("B2 multi-ev verified reason", "readable_false_verified" in blob9)
        check("B2 multi-ev no excerpt reason", "readable_false_excerpt" not in blob9)

        # 10) Multiple knowledge objects depend on same unreadable evidence
        pkg10 = build_valid_minimal_package(root / "multi_know")
        _set_source_readable(pkg10, "src_001", False)
        _set_excerpt(pkg10, "ev_001", "")
        claims = {
            "claims": [
                {
                    "claim_id": "claim_001",
                    "statement": {"text": "same support", "lang": "en"},
                    "status": "verified",
                    "evidence_ids": ["ev_001"],
                    "confirmation": None,
                    "related_fact_ids": [],
                    "conflict_ids": [],
                    "notes": "",
                }
            ]
        }
        save_json(pkg10 / "knowledge/claims.json", claims)
        ev10 = load_json(pkg10 / "evidence/evidence.json")
        ev10["evidence"][0]["supports"] = [
            {"type": "fact", "id": "fact_001"},
            {"type": "claim", "id": "claim_001"},
        ]
        save_json(pkg10 / "evidence/evidence.json", ev10)
        report10 = validate_package(pkg10)
        expect_status(report10, "I16", "FAIL", "B2 multi-knowledge same evidence FAIL")
        msgs = " ".join(e["message"] for e in result_map(report10)["I16"].get("errors", []))
        check("B2 multi-know mentions fact", "fact_001" in msgs)
        check("B2 multi-know mentions claim", "claim_001" in msgs)

        # 11) source not loaded → NOT_CHECKED
        pkg11 = build_valid_minimal_package(root / "no_src")
        (pkg11 / "source/source-index.json").unlink()
        report11 = validate_package(pkg11)
        expect_status(report11, "I16", "NOT_CHECKED", "B2 source unloaded NOT_CHECKED")

        # 12) evidence not loaded → NOT_CHECKED
        pkg12 = build_valid_minimal_package(root / "no_ev")
        (pkg12 / "evidence/evidence.json").unlink()
        report12 = validate_package(pkg12)
        expect_status(report12, "I16", "NOT_CHECKED", "B2 evidence unloaded NOT_CHECKED")

        # 13) knowledge not fully loaded → NOT_CHECKED (no Evidence FAIL on readable:true)
        pkg13 = build_valid_minimal_package(root / "no_know")
        (pkg13 / "knowledge/facts.json").unlink()
        report13 = validate_package(pkg13)
        expect_status(report13, "I16", "NOT_CHECKED", "B2 knowledge unloaded NOT_CHECKED")

        # 13b) knowledge unloaded but Evidence FAIL still reports FAIL
        pkg13b = build_valid_minimal_package(root / "no_know_evfail")
        _set_source_readable(pkg13b, "src_001", False)
        (pkg13b / "knowledge/claims.json").unlink()
        report13b = validate_package(pkg13b)
        expect_status(report13b, "I16", "FAIL", "B2 knowledge unload + excerpt still FAIL")

        # 14) fully loaded empty sets → PASS (already in empty package)
        empty = build_valid_minimal_package(root / "empty_i16", empty=True)
        report_e = validate_package(empty)
        expect_status(report_e, "I16", "PASS", "B2 empty collections I16 PASS")

        # 15) unknown source_id → I09 FAIL, I16 must not add readable:false FAIL
        pkg15 = build_valid_minimal_package(root / "unknown_src")
        ev15 = load_json(pkg15 / "evidence/evidence.json")
        ev15["evidence"][0]["locator"]["source_id"] = "src_missing"
        save_json(pkg15 / "evidence/evidence.json", ev15)
        _set_fact_status(pkg15, "fact_001", "unverified")
        facts15 = load_json(pkg15 / "knowledge/facts.json")
        facts15["facts"][0]["evidence_ids"] = []
        save_json(pkg15 / "knowledge/facts.json", facts15)
        ev15 = load_json(pkg15 / "evidence/evidence.json")
        ev15["evidence"][0]["supports"] = []
        save_json(pkg15 / "evidence/evidence.json", ev15)
        report15 = validate_package(pkg15)
        expect_status(report15, "I09", "FAIL", "B2 unknown source I09 FAIL")
        expect_status(report15, "I16", "PASS", "B2 unknown source not I16 FAIL")
        check(
            "B2 unknown no readable_false reasons",
            "readable_false" not in json.dumps(result_map(report15).get("I16", {})),
        )


def _patch_locator(pkg: Path, **fields) -> None:
    ev = load_json(pkg / "evidence/evidence.json")
    loc = ev["evidence"][0]["locator"]
    for k, v in fields.items():
        loc[k] = v
    save_json(pkg / "evidence/evidence.json", ev)


def _i12_errors(report: dict) -> list[dict]:
    return result_map(report).get("I12", {}).get("errors") or []


def _i12_msgs(report: dict) -> str:
    return " ".join(e.get("message", "") for e in _i12_errors(report))


def test_b3_i12_line_range() -> None:
    from _integrity import PackageIndex, check_i12, line_number_value

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1) Legal line_range
        pkg = build_valid_minimal_package(root / "ok")
        report = validate_package(pkg)
        expect_status(report, "I12", "PASS", "B3 legal line_range PASS")

        # 2) start=null
        pkg2 = build_valid_minimal_package(root / "start_null")
        _patch_locator(pkg2, start=None)
        report2 = validate_package(pkg2)
        expect_status(report2, "I12", "FAIL", "B3 start=null FAIL")
        check("B3 start=null reason", "line_range_null" in _i12_msgs(report2))

        # 3) end=null (no coalesce to start)
        pkg3 = build_valid_minimal_package(root / "end_null")
        _patch_locator(pkg3, end=None)
        report3 = validate_package(pkg3)
        expect_status(report3, "I12", "FAIL", "B3 end=null FAIL")
        check("B3 end=null reason", "line_range_null" in _i12_msgs(report3))

        # 4) start=0
        pkg4 = build_valid_minimal_package(root / "start0")
        _patch_locator(pkg4, start=0, end=1)
        report4 = validate_package(pkg4)
        expect_status(report4, "I12", "FAIL", "B3 start=0 FAIL")
        check("B3 start=0 reason", "line_range_start_lt_1" in _i12_msgs(report4))

        # 5) start negative
        pkg5 = build_valid_minimal_package(root / "start_neg")
        _patch_locator(pkg5, start=-1, end=1)
        report5 = validate_package(pkg5)
        expect_status(report5, "I12", "FAIL", "B3 start negative FAIL")
        check("B3 start neg reason", "line_range_start_lt_1" in _i12_msgs(report5))

        # 6) end < start
        pkg6 = build_valid_minimal_package(root / "end_lt")
        _patch_locator(pkg6, start=2, end=1)
        report6 = validate_package(pkg6)
        expect_status(report6, "I12", "FAIL", "B3 end < start FAIL")
        check("B3 end<start reason", "line_range_end_lt_start" in _i12_msgs(report6))

        # 7) end > line count (design.md has 2 lines)
        pkg7 = build_valid_minimal_package(root / "end_gt")
        _patch_locator(pkg7, start=1, end=99)
        report7 = validate_package(pkg7)
        expect_status(report7, "I12", "FAIL", "B3 end > lines FAIL")
        check("B3 out of bounds reason", "line_range_out_of_bounds" in _i12_msgs(report7))

        # 8) empty file
        pkg8 = build_valid_minimal_package(root / "empty_file")
        (pkg8 / "source/original/design.md").write_text("", encoding="utf-8")
        _patch_locator(pkg8, start=1, end=1)
        report8 = validate_package(pkg8)
        expect_status(report8, "I12", "FAIL", "B3 empty file FAIL")
        check("B3 empty file bounds", "line_range_out_of_bounds" in _i12_msgs(report8))

        # 9) 1.0 integer semantics — JSON number 1.0 may serialize as 1; force float via direct check
        kind, n = line_number_value(1.0)
        check("B3 1.0 ok", kind == "ok" and n == 1)
        pkg9 = build_valid_minimal_package(root / "one_point_zero")
        # After JSON round-trip 1.0 may become 1; still PASS either way
        _patch_locator(pkg9, start=1.0, end=1.0)
        report9 = validate_package(pkg9)
        expect_status(report9, "I12", "PASS", "B3 1.0 PASS")

        # 10) 1.5 illegal
        pkg10 = build_valid_minimal_package(root / "one_point_five")
        _patch_locator(pkg10, start=1.5, end=2)
        report10 = validate_package(pkg10)
        expect_status(report10, "I12", "FAIL", "B3 1.5 FAIL")
        check("B3 1.5 reason", "line_range_invalid" in _i12_msgs(report10))

        # 11) NaN / Infinity — direct classifier + check_i12 (JSON cannot carry these)
        check("B3 nan invalid", line_number_value(float("nan"))[0] == "invalid")
        check("B3 inf invalid", line_number_value(float("inf"))[0] == "invalid")
        pkg11 = build_valid_minimal_package(root / "nan_pkg")
        idx11 = PackageIndex()
        idx11.loaded_kinds.add("evidence")
        idx11.by_kind["evidence"] = {
            "ev_001": {
                "evidence_id": "ev_001",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "line_range",
                    "start": float("nan"),
                    "end": 1,
                    "excerpt": "x",
                },
            }
        }
        out11, _, _ = check_i12(idx11, pkg11, {"ev_001": "safe"})
        check("B3 nan I12 FAIL", out11.result == "FAIL", out11.message)
        check("B3 nan reason", "line_range_invalid" in (out11.errors[0]["message"] if out11.errors else ""))

        # 12) bool line numbers
        check("B3 True invalid", line_number_value(True)[0] == "invalid")
        check("B3 False invalid", line_number_value(False)[0] == "invalid")
        idx12 = PackageIndex()
        idx12.loaded_kinds.add("evidence")
        idx12.by_kind["evidence"] = {
            "ev_001": {
                "evidence_id": "ev_001",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "line_range",
                    "start": True,
                    "end": 1,
                    "excerpt": "x",
                },
            }
        }
        out12, _, _ = check_i12(idx12, pkg11, {"ev_001": "safe"})
        check("B3 bool I12 FAIL", out12.result == "FAIL", out12.message)

        # 13) I11 unsafe gate — no out-of-package read
        pkg13 = build_valid_minimal_package(root / "i11_unsafe")
        outside = root / "secret_outside.txt"
        outside.write_text("SECRET\n", encoding="utf-8")
        before = outside.read_text(encoding="utf-8")
        _patch_locator(pkg13, path="../secret_outside.txt", start=1, end=1)
        report13 = validate_package(pkg13)
        after = outside.read_text(encoding="utf-8")
        expect_status(report13, "I11", "FAIL", "B3 I11 unsafe still FAIL")
        expect_status(report13, "I12", "NOT_CHECKED", "B3 I11 unsafe → I12 NOT_CHECKED")
        check("B3 I11 gate reason", "i11_unsafe" in _i12_msgs(report13))
        check("B3 no outside mutate", before == after)

        # 14) I11 unresolved gate — inject safety map
        out14, _, _ = check_i12(idx11, pkg11, {"ev_001": "unresolved"})
        # fix idx to have valid numbers so gate is the only issue
        idx14 = PackageIndex()
        idx14.loaded_kinds.add("evidence")
        idx14.by_kind["evidence"] = {
            "ev_001": {
                "evidence_id": "ev_001",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "x",
                },
            }
        }
        out14, _, _ = check_i12(idx14, pkg11, {"ev_001": "unresolved"})
        check("B3 I11 unresolved NOT_CHECKED", out14.result == "NOT_CHECKED", out14.message)
        check("B3 i11_unresolved reason", "i11_unresolved" in out14.errors[0]["message"])

        # 15) I10 missing file
        pkg15 = build_valid_minimal_package(root / "i10_miss")
        _patch_locator(pkg15, path="source/original/missing.md", start=1, end=1)
        report15 = validate_package(pkg15)
        expect_status(report15, "I11", "PASS", "B3 missing path I11 PASS")
        expect_status(report15, "I10", "FAIL", "B3 missing path I10 FAIL")
        expect_status(report15, "I12", "NOT_CHECKED", "B3 I10 missing → I12 NOT_CHECKED")
        check("B3 i10_missing reason", "i10_missing" in _i12_msgs(report15))

        # 16) file read failure (OSError) → NOT_CHECKED read_failed
        pkg16 = build_valid_minimal_package(root / "read_fail")
        idx16 = PackageIndex()
        idx16.loaded_kinds.add("evidence")
        idx16.by_kind["evidence"] = {
            "ev_001": {
                "evidence_id": "ev_001",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "x",
                },
            }
        }
        real_read_text = Path.read_text

        def boom(self, *args, **kwargs):
            raise OSError("simulated read failure")

        Path.read_text = boom  # type: ignore[method-assign]
        try:
            out16, _, snap16 = check_i12(idx16, pkg16, {"ev_001": "safe"})
        finally:
            Path.read_text = real_read_text  # type: ignore[method-assign]
        check("B3 file read failure NOT_CHECKED", out16.result == "NOT_CHECKED", out16.message)
        check("B3 read_failed reason", "read_failed" in out16.errors[0]["message"])
        check("B3 read fail no snapshot", "ev_001" not in snap16)

        # 17) UTF-8 decode failure
        pkg17 = build_valid_minimal_package(root / "utf8_bad")
        bad = pkg17 / "source/original/design.md"
        bad.write_bytes(b"\xff\xfe binary not utf8 \xff")
        _patch_locator(pkg17, start=1, end=1)
        report17 = validate_package(pkg17)
        expect_status(report17, "I12", "NOT_CHECKED", "B3 utf8 fail NOT_CHECKED")
        check("B3 utf8 reason", "utf8_decode_failed" in _i12_msgs(report17))

        # 18) non line_range skipped → PASS (empty applicable)
        pkg18 = build_valid_minimal_package(root / "section_only")
        _patch_locator(
            pkg18,
            locator_type="section",
            start="Intro",
            end=None,
        )
        report18 = validate_package(pkg18)
        expect_status(report18, "I12", "PASS", "B3 non-line_range PASS")
        check("B3 section empty applicable", "empty applicable" in result_map(report18)["I12"]["message"])

        # 19) no applicable — empty evidence already PASS
        empty = build_valid_minimal_package(root / "empty_ev", empty=True)
        report19 = validate_package(empty)
        expect_status(report19, "I12", "PASS", "B3 empty evidence I12 PASS")

        # 20) evidence not loaded
        pkg20 = build_valid_minimal_package(root / "no_ev")
        (pkg20 / "evidence/evidence.json").unlink()
        report20 = validate_package(pkg20)
        expect_status(report20, "I12", "NOT_CHECKED", "B3 evidence unloaded NOT_CHECKED")

        # 21–22) mixed FAIL + NOT_CHECKED — retain both details; overall FAIL
        pkg21 = build_valid_minimal_package(root / "mixed")
        (pkg21 / "source/original/extra.md").write_text("only\n", encoding="utf-8")
        ev21 = load_json(pkg21 / "evidence/evidence.json")
        # ev_001: out of bounds FAIL
        ev21["evidence"][0]["locator"]["start"] = 1
        ev21["evidence"][0]["locator"]["end"] = 99
        # ev_002: I11 unsafe → NOT_CHECKED
        ev21["evidence"].append(
            {
                "evidence_id": "ev_002",
                "kind": "excerpt",
                "locator": {
                    "source_id": "src_001",
                    "path": "../outside.txt",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "x",
                },
                "supports": [],
                "redaction_applied": False,
                "notes": "",
            }
        )
        # ev_003: valid PASS item
        ev21["evidence"].append(
            {
                "evidence_id": "ev_003",
                "kind": "excerpt",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/extra.md",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "only",
                },
                "supports": [],
                "redaction_applied": False,
                "notes": "",
            }
        )
        save_json(pkg21 / "evidence/evidence.json", ev21)
        # break reverse links for I04 noise — set fact unverified empty
        facts = load_json(pkg21 / "knowledge/facts.json")
        facts["facts"][0]["evidence_ids"] = []
        facts["facts"][0]["status"] = "unverified"
        save_json(pkg21 / "knowledge/facts.json", facts)
        ev21 = load_json(pkg21 / "evidence/evidence.json")
        ev21["evidence"][0]["supports"] = []
        save_json(pkg21 / "evidence/evidence.json", ev21)
        report21 = validate_package(pkg21)
        expect_status(report21, "I12", "FAIL", "B3 mixed overall FAIL")
        msgs21 = _i12_msgs(report21)
        check("B3 mixed keeps FAIL detail", "line_range_out_of_bounds" in msgs21)
        check("B3 mixed keeps NOT_CHECKED detail", "i11_unsafe" in msgs21)
        check("B3 mixed message notes not checked", "not checked" in result_map(report21)["I12"]["message"])
        check(
            "B3 wrote_to_package false",
            report21["wrote_to_package"] is False,
        )
        check("B3 network false", report21["checker"]["network"] is False)


def _i13_errors(report: dict) -> list[dict]:
    return result_map(report).get("I13", {}).get("errors") or []


def _i13_msgs(report: dict) -> str:
    return " ".join(e.get("message", "") for e in _i13_errors(report))


def _set_locator_as(
    pkg: Path,
    locator_type: str,
    *,
    start=None,
    end=None,
    path: str | None = None,
) -> None:
    """Retarget first evidence locator to a non-line_range type (schema-valid)."""
    fields: dict = {"locator_type": locator_type}
    if path is not None:
        fields["path"] = path
    if locator_type == "section":
        fields["start"] = "Intro" if start is None else start
        fields["end"] = end
    elif locator_type == "json_pointer":
        fields["start"] = "/a/b" if start is None else start
        fields["end"] = end
    elif locator_type == "anchor":
        fields["start"] = "sec-1" if start is None else start
        fields["end"] = end
    elif locator_type == "page_range":
        fields["start"] = 1 if start is None else start
        fields["end"] = 1 if end is None else end
    _patch_locator(pkg, **fields)


def test_b4_i13_other_locators() -> None:
    from _integrity import PackageIndex, check_i13
    from pathlib import Path as PathType

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1) evidence unloaded → NOT_CHECKED
        pkg1 = build_valid_minimal_package(root / "no_ev")
        (pkg1 / "evidence/evidence.json").unlink()
        report1 = validate_package(pkg1)
        expect_status(report1, "I13", "NOT_CHECKED", "B4 evidence unloaded NOT_CHECKED")

        # 2) empty evidence loaded → PASS
        empty = build_valid_minimal_package(root / "empty", empty=True)
        report2 = validate_package(empty)
        expect_status(report2, "I13", "PASS", "B4 empty evidence PASS")

        # 3) only line_range → PASS (I12 still owns bounds)
        pkg3 = build_valid_minimal_package(root / "line_only")
        report3 = validate_package(pkg3)
        expect_status(report3, "I13", "PASS", "B4 line_range only I13 PASS")
        expect_status(report3, "I12", "PASS", "B4 line_range only I12 PASS")

        # 4–7) each applicable type alone → NOT_CHECKED
        for lt, label in [
            ("section", "section"),
            ("json_pointer", "json_pointer"),
            ("anchor", "anchor"),
            ("page_range", "page_range"),
        ]:
            pkg = build_valid_minimal_package(root / f"only_{lt}")
            _set_locator_as(pkg, lt)
            # avoid I16/I04 noise: drop verified link if needed — keep package schema-ok
            facts = load_json(pkg / "knowledge/facts.json")
            facts["facts"][0]["status"] = "unverified"
            facts["facts"][0]["evidence_ids"] = []
            save_json(pkg / "knowledge/facts.json", facts)
            ev = load_json(pkg / "evidence/evidence.json")
            ev["evidence"][0]["supports"] = []
            save_json(pkg / "evidence/evidence.json", ev)
            report = validate_package(pkg)
            expect_status(report, "I13", "NOT_CHECKED", f"B4 only {label} NOT_CHECKED")
            check(f"B4 only {label} no_finder", "no_finder" in _i13_msgs(report))
            check(f"B4 only {label} not PASS", report["checks"] is not None)

        # 8) four types mixed → NOT_CHECKED with four details
        pkg8 = build_valid_minimal_package(root / "four_types")
        (pkg8 / "source/original/extra.md").write_text("# H\n", encoding="utf-8")
        facts8 = load_json(pkg8 / "knowledge/facts.json")
        facts8["facts"][0]["status"] = "unverified"
        facts8["facts"][0]["evidence_ids"] = []
        save_json(pkg8 / "knowledge/facts.json", facts8)
        ev8 = {
            "evidence": [
                {
                    "evidence_id": "ev_sec",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "section",
                        "start": "Intro",
                        "end": None,
                        "excerpt": "x",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_ptr",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "json_pointer",
                        "start": "/a",
                        "end": None,
                        "excerpt": "x",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_anc",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "anchor",
                        "start": "a1",
                        "end": None,
                        "excerpt": "x",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_page",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "page_range",
                        "start": 1,
                        "end": 1,
                        "excerpt": "x",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
            ]
        }
        save_json(pkg8 / "evidence/evidence.json", ev8)
        report8 = validate_package(pkg8)
        expect_status(report8, "I13", "NOT_CHECKED", "B4 four types NOT_CHECKED")
        errs8 = _i13_errors(report8)
        check("B4 four types detail count", len(errs8) == 4, str(len(errs8)))
        ids8 = " ".join(e["message"] for e in errs8)
        for eid in ("ev_sec", "ev_ptr", "ev_anc", "ev_page"):
            check(f"B4 four types has {eid}", eid in ids8)

        # 9) line_range + section → I13 NOT_CHECKED; I12 still evaluates line_range
        pkg9 = build_valid_minimal_package(root / "mixed_lr")
        facts9 = load_json(pkg9 / "knowledge/facts.json")
        facts9["facts"][0]["status"] = "unverified"
        facts9["facts"][0]["evidence_ids"] = []
        save_json(pkg9 / "knowledge/facts.json", facts9)
        ev9 = load_json(pkg9 / "evidence/evidence.json")
        ev9["evidence"][0]["supports"] = []
        ev9["evidence"].append(
            {
                "evidence_id": "ev_sec",
                "kind": "excerpt",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "section",
                    "start": "Intro",
                    "end": None,
                    "excerpt": "x",
                },
                "supports": [],
                "redaction_applied": False,
                "notes": "",
            }
        )
        save_json(pkg9 / "evidence/evidence.json", ev9)
        report9 = validate_package(pkg9)
        expect_status(report9, "I13", "NOT_CHECKED", "B4 line+section I13 NOT_CHECKED")
        expect_status(report9, "I12", "PASS", "B4 line+section I12 still PASS")
        check("B4 mixed only section in I13", "ev_sec" in _i13_msgs(report9))
        check("B4 mixed no ev_001 in I13", "ev_001" not in _i13_msgs(report9))

        # 10–11) applicable never PASS; per-item detail present (covered above)

        # 12) I13 does not re-run I12: bad line_range still I12 FAIL, I13 PASS if no other types
        pkg12 = build_valid_minimal_package(root / "i12_own")
        _patch_locator(pkg12, start=1, end=99)
        report12 = validate_package(pkg12)
        expect_status(report12, "I12", "FAIL", "B4 I12 owns line_range FAIL")
        expect_status(report12, "I13", "PASS", "B4 I13 ignores line_range")

        # 13) no file content reads during check_i13
        pkg13 = build_valid_minimal_package(root / "no_read")
        idx13 = PackageIndex()
        idx13.loaded_kinds.add("evidence")
        idx13.by_kind["evidence"] = {
            "ev_sec": {
                "evidence_id": "ev_sec",
                "locator": {
                    "source_id": "src_001",
                    "path": "source/original/design.md",
                    "locator_type": "section",
                    "start": "Intro",
                    "end": None,
                    "excerpt": "x",
                },
            }
        }
        reads: list[str] = []
        real_read = PathType.read_text

        def counting_read(self, *args, **kwargs):
            reads.append(str(self))
            return real_read(self, *args, **kwargs)

        PathType.read_text = counting_read  # type: ignore[method-assign]
        try:
            out13 = check_i13(idx13, {"ev_sec": "safe"})
        finally:
            PathType.read_text = real_read  # type: ignore[method-assign]
        check("B4 no content read", reads == [], str(reads))
        check("B4 unit NOT_CHECKED", out13.result == "NOT_CHECKED", out13.message)

        # 14) no out-of-package access: unsafe path still NOT_CHECKED without reading
        outside = root / "outside_secret.txt"
        outside.write_text("SECRET\n", encoding="utf-8")
        before = outside.read_text(encoding="utf-8")
        idx14 = PackageIndex()
        idx14.loaded_kinds.add("evidence")
        idx14.by_kind["evidence"] = {
            "ev_bad": {
                "evidence_id": "ev_bad",
                "locator": {
                    "source_id": "src_001",
                    "path": "../outside_secret.txt",
                    "locator_type": "section",
                    "start": "X",
                    "end": None,
                    "excerpt": "x",
                },
            }
        }
        out14 = check_i13(idx14, {"ev_bad": "unsafe"})
        after = outside.read_text(encoding="utf-8")
        check("B4 outside unchanged", before == after)
        check("B4 unsafe gate reason", "i11_unsafe" in out14.errors[0]["message"])
        check("B4 unsafe NOT_CHECKED", out14.result == "NOT_CHECKED")

        # 15–16) package flags
        report15 = validate_package(pkg3)
        check("B4 wrote_to_package false", report15["wrote_to_package"] is False)
        check("B4 network false", report15["checker"]["network"] is False)
        check("B4 phase", report15["checker"]["phase"] == "3B-C2")


def _i14_errors(report: dict) -> list[dict]:
    return result_map(report).get("I14", {}).get("errors") or []


def _i14_msgs(report: dict) -> str:
    return " ".join(e.get("message", "") for e in _i14_errors(report))


def _write_design(pkg: Path, text: str) -> None:
    (pkg / "source/original/design.md").write_text(text, encoding="utf-8", newline="\n")


def _unlink_knowledge_links(pkg: Path) -> None:
    facts = load_json(pkg / "knowledge/facts.json")
    if facts.get("facts"):
        facts["facts"][0]["status"] = "unverified"
        facts["facts"][0]["evidence_ids"] = []
        save_json(pkg / "knowledge/facts.json", facts)
    ev = load_json(pkg / "evidence/evidence.json")
    if ev.get("evidence"):
        ev["evidence"][0]["supports"] = []
        save_json(pkg / "evidence/evidence.json", ev)


def test_c1_i14_excerpt_match() -> None:
    """I14 excerpt match — IDs map to docs/validator-i14-test-plan.zh-CN.md."""
    from _integrity import (
        PackageIndex,
        check_i12,
        check_i14,
        excerpt_nonempty_lines,
        normalize_excerpt_newlines,
    )
    from pathlib import Path as PathType
    import unicodedata

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # --- Gates first ---
        # I14-T068 / T085: evidence unloaded
        pkg_u = build_valid_minimal_package(root / "unload")
        (pkg_u / "evidence/evidence.json").unlink()
        report_u = validate_package(pkg_u)
        expect_status(report_u, "I14", "NOT_CHECKED", "I14-T068 evidence unloaded")

        # I14-T070 / T084 / T069: empty loaded → PASS
        empty = build_valid_minimal_package(root / "empty", empty=True)
        report_e = validate_package(empty)
        expect_status(report_e, "I14", "PASS", "I14-T070 empty loaded PASS")

        # I14-T060 / T073: unsafe, zero I14 content read
        idx_unsafe = PackageIndex()
        idx_unsafe.loaded_kinds.add("evidence")
        idx_unsafe.by_kind["evidence"] = {
            "ev_bad": {
                "evidence_id": "ev_bad",
                "locator": {
                    "source_id": "src_001",
                    "path": "../outside_secret.txt",
                    "locator_type": "line_range",
                    "start": 1,
                    "end": 1,
                    "excerpt": "x",
                },
            }
        }
        reads: list[str] = []
        real_read = PathType.read_text

        def counting_read(self, *args, **kwargs):
            reads.append(str(self))
            return real_read(self, *args, **kwargs)

        PathType.read_text = counting_read  # type: ignore[method-assign]
        try:
            out_u = check_i14(
                idx_unsafe,
                root / "unload",
                {"ev_bad": "unsafe"},
                {"ev_bad": "not_checked"},
            )
        finally:
            PathType.read_text = real_read  # type: ignore[method-assign]
        check("I14-T060 unsafe NC", out_u.result == "NOT_CHECKED")
        check("I14-T060 i11_unsafe", "i11_unsafe" in out_u.errors[0]["message"])
        check("I14-T073 zero reads", reads == [], str(reads))

        # I14-T061 unresolved
        out_ur = check_i14(
            idx_unsafe,
            root / "unload",
            {"ev_bad": "unresolved"},
            {"ev_bad": "not_checked"},
        )
        check("I14-T061 unresolved", out_ur.result == "NOT_CHECKED")
        check("I14-T061 reason", "i11_unresolved" in out_ur.errors[0]["message"])

        # I14-T062 i10 missing → I12 not_checked → I14 consumes I12
        pkg_miss = build_valid_minimal_package(root / "miss")
        _patch_locator(pkg_miss, path="source/original/nope.md")
        report_miss = validate_package(pkg_miss)
        expect_status(report_miss, "I14", "NOT_CHECKED", "I14-T062 i10 missing")
        check("I14-T062 reason", "i12_not_checked" in _i14_msgs(report_miss))

        # I14-T063 null start → i12_failed
        pkg_null = build_valid_minimal_package(root / "null")
        _patch_locator(pkg_null, start=None)
        report_null = validate_package(pkg_null)
        expect_status(report_null, "I12", "FAIL", "I14-T063 I12 FAIL")
        expect_status(report_null, "I14", "NOT_CHECKED", "I14-T063 I14 NC")
        check("I14-T063 i12_failed", "i12_failed" in _i14_msgs(report_null))

        # I14-T064 / T098 out of bounds
        pkg_oob = build_valid_minimal_package(root / "oob")
        _patch_locator(pkg_oob, start=1, end=99)
        report_oob = validate_package(pkg_oob)
        expect_status(report_oob, "I12", "FAIL", "I14-T064 I12 FAIL")
        expect_status(report_oob, "I14", "NOT_CHECKED", "I14-T098 I14 NC not excerpt FAIL")
        check("I14-T064 no excerpt_line_missing", "excerpt_line_missing" not in _i14_msgs(report_oob))
        check("I14-T064 i12_failed", "i12_failed" in _i14_msgs(report_oob))

        # I14-T065 end < start
        pkg_ord = build_valid_minimal_package(root / "ord")
        _patch_locator(pkg_ord, start=2, end=1)
        report_ord = validate_package(pkg_ord)
        expect_status(report_ord, "I14", "NOT_CHECKED", "I14-T065 end<start")
        check("I14-T065 i12_failed", "i12_failed" in _i14_msgs(report_ord))

        # I14-T005 empty file → I12 FAIL → I14 NC
        pkg_emptyf = build_valid_minimal_package(root / "emptyf")
        _write_design(pkg_emptyf, "")
        _patch_locator(pkg_emptyf, start=1, end=1, excerpt="x")
        report_emptyf = validate_package(pkg_emptyf)
        expect_status(report_emptyf, "I12", "FAIL", "I14-T005 I12 FAIL empty file")
        expect_status(report_emptyf, "I14", "NOT_CHECKED", "I14-T005 I14 NC")
        check("I14-T005 i12_failed", "i12_failed" in _i14_msgs(report_emptyf))

        # I14-T066 / T071: I11/I10 PASS, I12 NC via bad UTF-8
        pkg_utf = build_valid_minimal_package(root / "utf")
        bad = pkg_utf / "source/original/design.md"
        bad.write_bytes(b"\xff\xfe not utf8")
        _patch_locator(pkg_utf, start=1, end=1, excerpt="x")
        report_utf = validate_package(pkg_utf)
        expect_status(report_utf, "I12", "NOT_CHECKED", "I14-T066 I12 NC")
        expect_status(report_utf, "I14", "NOT_CHECKED", "I14-T066/T071 I14 NC")
        check("I14-T071 i12_not_checked", "i12_not_checked" in _i14_msgs(report_utf))
        check(
            "I14-T071 not utf8_decode_failed",
            "utf8_decode_failed" not in _i14_msgs(report_utf),
        )

        # I14-T067 readable:false
        pkg_rf = build_valid_minimal_package(root / "rf")
        _set_source_readable(pkg_rf, "src_001", False)
        _unlink_knowledge_links(pkg_rf)
        _patch_locator(pkg_rf, excerpt="")  # avoid I16 evidence quoting FAIL noise optional
        # non-empty excerpt for I14 gate; I16 may FAIL quoting — restore non-empty
        _patch_locator(pkg_rf, excerpt="生产环境服务默认监听 8080 端口。")
        report_rf = validate_package(pkg_rf)
        expect_status(report_rf, "I14", "NOT_CHECKED", "I14-T067 readable_false")
        check("I14-T067 reason", "readable_false" in _i14_msgs(report_rf))
        check("I14-T097 I16 still fails quoting", result_map(report_rf)["I16"]["result"] == "FAIL")

        # I14-T072 / T074: I12 read failure → no snapshot; I14 must not re-read
        pkg72 = build_valid_minimal_package(root / "r72")
        _write_design(pkg72, "line1\nline2\n")
        _patch_locator(pkg72, start=2, end=2, excerpt="line2")
        idx72 = PackageIndex()
        idx72.loaded_kinds.add("evidence")
        idx72.loaded_kinds.add("source")
        idx72.by_kind["source"] = {
            "src_001": {"source_id": "src_001", "readable": True},
        }
        idx72.by_kind["evidence"] = {
            "ev_001": load_json(pkg72 / "evidence/evidence.json")["evidence"][0],
        }
        real_read2 = PathType.read_text

        def fail_os(self, *args, **kwargs):
            if Path(self).name == "design.md":
                raise OSError("simulated")
            return real_read2(self, *args, **kwargs)

        PathType.read_text = fail_os  # type: ignore[method-assign]
        try:
            _c72, st72, snap72 = check_i12(idx72, pkg72, {"ev_001": "safe"})
        finally:
            PathType.read_text = real_read2  # type: ignore[method-assign]
        i14_reads_72: list[str] = []

        def count_i14_72(self, *args, **kwargs):
            i14_reads_72.append(Path(self).name)
            return real_read2(self, *args, **kwargs)

        PathType.read_text = count_i14_72  # type: ignore[method-assign]
        try:
            out72 = check_i14(idx72, pkg72, {"ev_001": "safe"}, st72, snap72)
        finally:
            PathType.read_text = real_read2  # type: ignore[method-assign]
        check("I14-T072 I12 NC", st72.get("ev_001") == "not_checked")
        check("I14-T072 no snapshot", "ev_001" not in snap72)
        check("I14-T072 I14 NC", out72.result == "NOT_CHECKED")
        check("I14-T072 reason", "i12_not_checked" in out72.errors[0]["message"])
        check("I14-T072 zero I14 reads", i14_reads_72 == [], str(i14_reads_72))

        def fail_utf(self, *args, **kwargs):
            if Path(self).name == "design.md":
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "sim")
            return real_read2(self, *args, **kwargs)

        PathType.read_text = fail_utf  # type: ignore[method-assign]
        try:
            _c74, st74, snap74 = check_i12(idx72, pkg72, {"ev_001": "safe"})
        finally:
            PathType.read_text = real_read2  # type: ignore[method-assign]
        i14_reads_74: list[str] = []

        def count_i14_74(self, *args, **kwargs):
            i14_reads_74.append(Path(self).name)
            return real_read2(self, *args, **kwargs)

        PathType.read_text = count_i14_74  # type: ignore[method-assign]
        try:
            out74 = check_i14(idx72, pkg72, {"ev_001": "safe"}, st74, snap74)
        finally:
            PathType.read_text = real_read2  # type: ignore[method-assign]
        check("I14-T074 I12 NC", st74.get("ev_001") == "not_checked")
        check("I14-T074 no snapshot", "ev_001" not in snap74)
        check("I14-T074 I14 NC", out74.result == "NOT_CHECKED")
        check("I14-T074 reason", "i12_not_checked" in out74.errors[0]["message"])
        check("I14-T074 zero I14 reads", i14_reads_74 == [], str(i14_reads_74))

        # source-index unloaded → cannot confirm readable → NC
        idx_ns = PackageIndex()
        idx_ns.loaded_kinds.add("evidence")
        idx_ns.by_kind["evidence"] = dict(idx72.by_kind["evidence"])
        out_ns = check_i14(
            idx_ns, pkg72, {"ev_001": "safe"}, {"ev_001": "pass"}, {"ev_001": "line2\n"}
        )
        check("I14 source unloaded NC", out_ns.result == "NOT_CHECKED")
        check(
            "I14 source_readable_unresolved",
            "source_readable_unresolved" in out_ns.errors[0]["message"],
        )

        # --- Matching ---
        pkg1 = build_valid_minimal_package(root / "t001")
        _write_design(pkg1, "A\nB\n")
        _patch_locator(pkg1, start=2, end=2, excerpt="B")
        expect_status(validate_package(pkg1), "I14", "PASS", "I14-T001 single line")

        pkg2 = build_valid_minimal_package(root / "t002")
        _write_design(pkg2, "A\nB\nC\n")
        _patch_locator(pkg2, start=1, end=3, excerpt="A\nC")
        expect_status(validate_package(pkg2), "I14", "PASS", "I14-T002 multiline")

        pkg3 = build_valid_minimal_package(root / "t003")
        _write_design(pkg3, "A\nB\n")
        _patch_locator(pkg3, start=1, end=1, excerpt="B")
        report3 = validate_package(pkg3)
        expect_status(report3, "I14", "FAIL", "I14-T003 missing")
        check("I14-T003 reason", "excerpt_line_missing" in _i14_msgs(report3))

        pkg4 = build_valid_minimal_package(root / "t004")
        _write_design(pkg4, "A\nB\n")
        _patch_locator(pkg4, start=1, end=2, excerpt="A\nZ")
        expect_status(validate_package(pkg4), "I14", "FAIL", "I14-T004 partial missing")

        pkg6 = build_valid_minimal_package(root / "t006")
        _write_design(pkg6, "xxYYxxYYxx\n")
        _patch_locator(pkg6, start=1, end=1, excerpt="YY")
        expect_status(validate_package(pkg6), "I14", "PASS", "I14-T006 repeated substr")

        pkg7 = build_valid_minimal_package(root / "t007")
        _write_design(pkg7, "hello world\n")
        _patch_locator(pkg7, start=1, end=1, excerpt="world")
        expect_status(validate_package(pkg7), "I14", "PASS", "I14-T007 substr not full line")

        pkg8 = build_valid_minimal_package(root / "t008")
        _write_design(pkg8, "secret\nother\n")
        _patch_locator(pkg8, start=2, end=2, excerpt="secret")
        expect_status(validate_package(pkg8), "I14", "FAIL", "I14-T008 outside window")

        # Newlines I14-T010–T015
        pkg_nl = build_valid_minimal_package(root / "nl")
        _write_design(pkg_nl, "a\nb\n")
        _patch_locator(pkg_nl, start=1, end=2, excerpt="a\nb")
        expect_status(validate_package(pkg_nl), "I14", "PASS", "I14-T010 LF")
        _patch_locator(pkg_nl, excerpt="a\r\nb")
        expect_status(validate_package(pkg_nl), "I14", "PASS", "I14-T011 CRLF")
        _patch_locator(pkg_nl, excerpt="a\rb")
        expect_status(validate_package(pkg_nl), "I14", "PASS", "I14-T012 CR")
        _patch_locator(pkg_nl, excerpt="a\r\nb\rc\n")
        _write_design(pkg_nl, "a\nb\nc\n")
        _patch_locator(pkg_nl, start=1, end=3, excerpt="a\r\nb\rc\n")
        expect_status(validate_package(pkg_nl), "I14", "PASS", "I14-T013 mixed")
        _patch_locator(pkg_nl, excerpt="a\n")
        expect_status(validate_package(pkg_nl), "I14", "PASS", "I14-T014 trailing nl")
        raw = "  keep  "
        lines = excerpt_nonempty_lines(raw + "\r\n")
        check("I14-T015 char content", lines == ["  keep  "], str(lines))
        check(
            "I14-T015 normalize only newlines",
            normalize_excerpt_newlines("x\r\ny") == "x\ny",
        )

        # Whitespace T020–T028
        pkg_ws = build_valid_minimal_package(root / "ws")
        _write_design(pkg_ws, "a  b\n")
        _patch_locator(pkg_ws, start=1, end=1, excerpt="")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T020 empty excerpt")
        _patch_locator(pkg_ws, excerpt="   ")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T021 spaces")
        _patch_locator(pkg_ws, excerpt="\t\t")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T022 tabs")
        _patch_locator(pkg_ws, excerpt="  \n\t\n")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T023 blank lines")
        _patch_locator(pkg_ws, excerpt="\n\na  b\n")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T024 blank+text")
        _patch_locator(pkg_ws, excerpt=" a  b")
        expect_status(validate_package(pkg_ws), "I14", "FAIL", "I14-T025 leading space")
        _patch_locator(pkg_ws, excerpt="a  b ")
        expect_status(validate_package(pkg_ws), "I14", "FAIL", "I14-T026 trailing space")
        _patch_locator(pkg_ws, excerpt="a  b")
        expect_status(validate_package(pkg_ws), "I14", "PASS", "I14-T027 multi space")
        _write_design(pkg_ws, "a b\n")
        _patch_locator(pkg_ws, excerpt="a  b")
        expect_status(validate_package(pkg_ws), "I14", "FAIL", "I14-T028 space mismatch")

        # Unicode T030–T034
        nfc = unicodedata.normalize("NFC", "é")
        nfd = unicodedata.normalize("NFD", "é")
        pkg_uc = build_valid_minimal_package(root / "uc")
        _write_design(pkg_uc, nfc + "\n")
        _patch_locator(pkg_uc, start=1, end=1, excerpt=nfc)
        expect_status(validate_package(pkg_uc), "I14", "PASS", "I14-T030 NFC=NFC")
        _write_design(pkg_uc, nfd + "\n")
        _patch_locator(pkg_uc, excerpt=nfd)
        expect_status(validate_package(pkg_uc), "I14", "PASS", "I14-T031 NFD=NFD")
        _write_design(pkg_uc, nfc + "\n")
        _patch_locator(pkg_uc, excerpt=nfd)
        expect_status(validate_package(pkg_uc), "I14", "FAIL", "I14-T032 NFC≠NFD")
        _write_design(pkg_uc, "端口 8080 ok\n")
        _patch_locator(pkg_uc, excerpt="端口 8080 ok")
        expect_status(validate_package(pkg_uc), "I14", "PASS", "I14-T033 zh-en")
        _patch_locator(pkg_uc, excerpt="端口 8081 ok")
        expect_status(validate_package(pkg_uc), "I14", "FAIL", "I14-T034 zh-en miss")

        # Order T035–T037
        pkg_ord2 = build_valid_minimal_package(root / "ord2")
        _write_design(pkg_ord2, "L1\nmiddle\nL3\n")
        _patch_locator(pkg_ord2, start=1, end=3, excerpt="L1\nL3")
        expect_status(validate_package(pkg_ord2), "I14", "PASS", "I14-T035 order")
        _patch_locator(pkg_ord2, excerpt="L3\nL1")
        expect_status(validate_package(pkg_ord2), "I14", "PASS", "I14-T036 reverse")
        _patch_locator(pkg_ord2, excerpt="L1\nL3")
        expect_status(validate_package(pkg_ord2), "I14", "PASS", "I14-T037 noncontig")

        # Types: non-line_range → I14 NOT_CHECKED (out_of_scope_type)
        def _only_type(name: str, lt: str, start, end) -> None:
            pkg = build_valid_minimal_package(root / name)
            _unlink_knowledge_links(pkg)
            ev = load_json(pkg / "evidence/evidence.json")
            ev["evidence"][0]["locator"] = {
                "source_id": "src_001",
                "path": "source/original/design.md",
                "locator_type": lt,
                "start": start,
                "end": end,
                "excerpt": "line1",
            }
            save_json(pkg / "evidence/evidence.json", ev)
            report = validate_package(pkg)
            expect_status(report, "I14", "NOT_CHECKED", f"I14 only {lt} NOT_CHECKED")
            check(
                f"I14 only {lt} out_of_scope",
                "out_of_scope_type" in _i14_msgs(report),
            )

        _only_type("sec", "section", "Intro", None)
        _only_type("jptr", "json_pointer", "/a", None)
        _only_type("anc", "anchor", "a1", None)
        _only_type("page", "page_range", 1, 1)

        # line_range PASS + section → overall NOT_CHECKED
        pkg_mix = build_valid_minimal_package(root / "lr_sec")
        _unlink_knowledge_links(pkg_mix)
        _write_design(pkg_mix, "A\nB\n")
        evm = {
            "evidence": [
                {
                    "evidence_id": "ev_lr",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 1,
                        "end": 1,
                        "excerpt": "A",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_sec",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "section",
                        "start": "Intro",
                        "end": None,
                        "excerpt": "A",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
            ]
        }
        save_json(pkg_mix / "evidence/evidence.json", evm)
        report_mix = validate_package(pkg_mix)
        expect_status(report_mix, "I14", "NOT_CHECKED", "I14 line_range+section NC")
        check("I14 mix has out_of_scope", "out_of_scope_type" in _i14_msgs(report_mix))
        expect_status(report_mix, "I13", "NOT_CHECKED", "I14-T096 I13 NC")

        # all line_range PASS, no other types → PASS
        pkg_lr_only = build_valid_minimal_package(root / "lr_only")
        _write_design(pkg_lr_only, "A\n")
        _patch_locator(pkg_lr_only, start=1, end=1, excerpt="A")
        expect_status(
            validate_package(pkg_lr_only),
            "I14",
            "PASS",
            "I14 all line_range only PASS",
        )

        # I12 overall FAIL must not block I14 on other I12-pass items
        pkg_partial = build_valid_minimal_package(root / "i12_partial")
        _unlink_knowledge_links(pkg_partial)
        _write_design(pkg_partial, "okline\n")
        evp = {
            "evidence": [
                {
                    "evidence_id": "ev_bad_bounds",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 1,
                        "end": 99,
                        "excerpt": "okline",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_ok",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 1,
                        "end": 1,
                        "excerpt": "okline",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
            ]
        }
        save_json(pkg_partial / "evidence/evidence.json", evp)
        report_p12 = validate_package(pkg_partial)
        expect_status(report_p12, "I12", "FAIL", "I14 I12 overall FAIL")
        expect_status(report_p12, "I14", "NOT_CHECKED", "I14 partial I12 still NC not FAIL")
        check("I14 partial has i12_failed", "i12_failed" in _i14_msgs(report_p12))
        check("I14 partial no excerpt FAIL", "excerpt_line_missing" not in _i14_msgs(report_p12))

        # T080–T083 rollup
        pkg_s = build_valid_minimal_package(root / "sum")
        _unlink_knowledge_links(pkg_s)
        _write_design(pkg_s, "A\nB\n")
        evs = {
            "evidence": [
                {
                    "evidence_id": "ev_ok",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 1,
                        "end": 1,
                        "excerpt": "A",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
                {
                    "evidence_id": "ev_bad",
                    "kind": "excerpt",
                    "locator": {
                        "source_id": "src_001",
                        "path": "source/original/design.md",
                        "locator_type": "line_range",
                        "start": 2,
                        "end": 2,
                        "excerpt": "Z",
                    },
                    "supports": [],
                    "redaction_applied": False,
                    "notes": "",
                },
            ]
        }
        save_json(pkg_s / "evidence/evidence.json", evs)
        expect_status(validate_package(pkg_s), "I14", "FAIL", "I14-T081 mix FAIL")

        evs["evidence"][1]["locator"]["path"] = "../outside.md"
        save_json(pkg_s / "evidence/evidence.json", evs)
        # first ok, second unsafe → NC overall (no FAIL)
        expect_status(validate_package(pkg_s), "I14", "NOT_CHECKED", "I14-T082 PASS+NC")

        evs["evidence"][0]["locator"]["excerpt"] = "NOPE"
        evs["evidence"][1]["locator"]["path"] = "../outside.md"
        save_json(pkg_s / "evidence/evidence.json", evs)
        expect_status(validate_package(pkg_s), "I14", "FAIL", "I14-T083 FAIL>NC")

        # T090–T092 privacy / readonly
        pkg_p = build_valid_minimal_package(root / "priv")
        _write_design(pkg_p, "visible\n")
        _patch_locator(pkg_p, start=1, end=1, excerpt="sk-test-SECRET-not-in-window")
        before = fingerprint_package(pkg_p)
        report_p = validate_package(pkg_p)
        after = fingerprint_package(pkg_p)
        check("I14-T090 fingerprint", before == after)
        check("I14-T090 wrote false", report_p["wrote_to_package"] is False)
        check("I14-T090 network", report_p["checker"]["network"] is False)
        check("I14-T090 read_only", report_p["read_only"] is True)
        expect_status(report_p, "I14", "FAIL", "I14-T092 FAIL with secret excerpt")
        dump = json.dumps(report_p, ensure_ascii=False)
        check("I14-T092 no secret leak", "sk-test-SECRET" not in dump)

        outside = root / "outside_secret.txt"
        outside.write_text("SECRET\n", encoding="utf-8")
        before_o = outside.read_text(encoding="utf-8")
        pkg_out = build_valid_minimal_package(root / "outpkg")
        _patch_locator(pkg_out, path="../outside_secret.txt")
        report_out = validate_package(pkg_out)
        after_o = outside.read_text(encoding="utf-8")
        check("I14-T091 outside unchanged", before_o == after_o)
        expect_status(report_out, "I14", "NOT_CHECKED", "I14-T091 unsafe NC")

        # T093 generated-output (pre-verified 22/22 match)
        with tempfile.TemporaryDirectory() as gtmp:
            gpkg = Path(gtmp) / "generated-output"
            shutil.copytree(GENERATED, gpkg)
            greport = validate_package(gpkg)
            expect_status(greport, "I14", "PASS", "I14-T093 generated PASS")
            check("I14-T093 L4 NC", greport["layers"]["L4"] == "NOT_CHECKED")
            lim = " ".join(greport.get("limitations") or [])
            check("I14-T093 limitations semantic", "semantic" in lim.lower() or "L4" in lim)

        # T094 minimal
        expect_status(
            validate_package(build_valid_minimal_package(root / "min2")),
            "I14",
            "PASS",
            "I14-T094 minimal",
        )

        # T095 smoke weaker: first line hits, second missing
        pkg95 = build_valid_minimal_package(root / "smoke")
        _write_design(pkg95, "first\nsecond\n")
        _patch_locator(pkg95, start=1, end=2, excerpt="first\nMISSING")
        expect_status(validate_package(pkg95), "I14", "FAIL", "I14-T095 stricter than smoke")

        # T099 / T086 / T100 flags
        report_f = validate_package(build_valid_minimal_package(root / "flags"))
        check("I14-T099 phase", report_f["checker"]["phase"] == "3B-C2")
        check(
            "I14-T099 L3_C_excerpts",
            report_f["checker"]["scripts_implemented"]["L3_C_excerpts"] is True,
        )
        expect_status(report_f, "I20", "NOT_CHECKED", "I14-T099 I20 zero applicable")
        i14r = result_map(report_f)["I14"]["result"]
        check("I14-T086 status set", i14r in {"PASS", "FAIL", "NOT_CHECKED"}, i14r)
        for hid in [f"H{i:02d}" for i in range(1, 7)]:
            expect_status(report_f, hid, "NOT_CHECKED", f"I14-T100 {hid}")

        # --- Snapshot consistency T101–T107 (real check_i12 → check_i14) ---
        pkg_snap = build_valid_minimal_package(root / "snap")
        _write_design(pkg_snap, "SNAP_OK\nSNAP_OTHER\n")
        _patch_locator(pkg_snap, start=1, end=1, excerpt="SNAP_OK")
        ev0 = load_json(pkg_snap / "evidence/evidence.json")["evidence"][0]
        src0 = load_json(pkg_snap / "source/source-index.json")["sources"][0]
        idx_snap = PackageIndex()
        idx_snap.loaded_kinds.add("evidence")
        idx_snap.loaded_kinds.add("source")
        idx_snap.by_kind["evidence"] = {ev0["evidence_id"]: ev0}
        idx_snap.by_kind["source"] = {src0["source_id"]: src0}
        eid = ev0["evidence_id"]
        safety_ok = {eid: "safe"}

        out_i12, st_i12, snap_i12 = check_i12(idx_snap, pkg_snap, safety_ok)
        check("I14-T101 I12 PASS", out_i12.result == "PASS")
        check("I14-T101 status pass", st_i12.get(eid) == "pass")
        check("I14-T101 has snapshot", eid in snap_i12 and "SNAP_OK" in snap_i12[eid])
        snap_obj_id = id(snap_i12[eid])

        i14_reads_101: list[str] = []
        real_rt = PathType.read_text

        def forbid_i14_read(self, *args, **kwargs):
            i14_reads_101.append(Path(self).name)
            raise AssertionError(f"I14 must not re-read {self}")

        PathType.read_text = forbid_i14_read  # type: ignore[method-assign]
        try:
            out_i14 = check_i14(idx_snap, pkg_snap, safety_ok, st_i12, snap_i12)
        finally:
            PathType.read_text = real_rt  # type: ignore[method-assign]
        check("I14-T101 I14 PASS", out_i14.result == "PASS", out_i14.message)
        check("I14-T101 zero I14 reads", i14_reads_101 == [], str(i14_reads_101))
        check("I14-T101 same snapshot object", id(snap_i12[eid]) == snap_obj_id)

        # I14-T102: full L3 — design.md content read once (I12 only)
        pkg102 = build_valid_minimal_package(root / "t102")
        _write_design(pkg102, "ONE\n")
        _patch_locator(pkg102, start=1, end=1, excerpt="ONE")
        design_reads: list[str] = []
        real_rt102 = PathType.read_text

        def count_design(self, *args, **kwargs):
            if Path(self).name == "design.md":
                design_reads.append("design.md")
            return real_rt102(self, *args, **kwargs)

        PathType.read_text = count_design  # type: ignore[method-assign]
        try:
            report102 = validate_package(pkg102)
        finally:
            PathType.read_text = real_rt102  # type: ignore[method-assign]
        expect_status(report102, "I12", "PASS", "I14-T102 I12 PASS")
        expect_status(report102, "I14", "PASS", "I14-T102 I14 PASS")
        check(
            "I14-T102 design.md read once",
            len(design_reads) == 1,
            f"reads={len(design_reads)} {design_reads}",
        )

        # I14-T103: I12 OSError → I14 NC, no re-read (real check_i12→check_i14)
        pkg103 = build_valid_minimal_package(root / "t103")
        _write_design(pkg103, "X\n")
        _patch_locator(pkg103, start=1, end=1, excerpt="X")
        ev103 = load_json(pkg103 / "evidence/evidence.json")["evidence"][0]
        src103 = load_json(pkg103 / "source/source-index.json")["sources"][0]
        idx103 = PackageIndex()
        idx103.loaded_kinds.add("evidence")
        idx103.loaded_kinds.add("source")
        idx103.by_kind["evidence"] = {ev103["evidence_id"]: ev103}
        idx103.by_kind["source"] = {src103["source_id"]: src103}
        eid103 = ev103["evidence_id"]

        def boom103(self, *args, **kwargs):
            if Path(self).name == "design.md":
                raise OSError("t103")
            return real_rt(self, *args, **kwargs)

        PathType.read_text = boom103  # type: ignore[method-assign]
        try:
            _c103, st103, snap103 = check_i12(idx103, pkg103, {eid103: "safe"})
        finally:
            PathType.read_text = real_rt  # type: ignore[method-assign]
        reads103: list[str] = []

        def count103(self, *args, **kwargs):
            reads103.append(Path(self).name)
            return real_rt(self, *args, **kwargs)

        PathType.read_text = count103  # type: ignore[method-assign]
        try:
            out103 = check_i14(idx103, pkg103, {eid103: "safe"}, st103, snap103)
        finally:
            PathType.read_text = real_rt  # type: ignore[method-assign]
        check("I14-T103 I12 not_checked", st103.get(eid103) == "not_checked")
        check("I14-T103 no snapshot", eid103 not in snap103)
        check("I14-T103 I14 NC", out103.result == "NOT_CHECKED")
        check("I14-T103 zero I14 reads", reads103 == [], str(reads103))

        # I14-T104: pass status but missing snapshot → NC, no remedial read
        reads104: list[str] = []

        def count104(self, *args, **kwargs):
            reads104.append(Path(self).name)
            return real_rt(self, *args, **kwargs)

        PathType.read_text = count104  # type: ignore[method-assign]
        try:
            out104 = check_i14(
                idx_snap, pkg_snap, safety_ok, {eid: "pass"}, {}
            )
        finally:
            PathType.read_text = real_rt  # type: ignore[method-assign]
        check("I14-T104 NC", out104.result == "NOT_CHECKED")
        check("I14-T104 snapshot_missing", "snapshot_missing" in out104.errors[0]["message"])
        check("I14-T104 zero reads", reads104 == [], str(reads104))

        # I14-T105: snapshot match → PASS (real check_i12→check_i14)
        pkg105 = build_valid_minimal_package(root / "t105")
        _write_design(pkg105, "MATCH_LINE\n")
        _patch_locator(pkg105, start=1, end=1, excerpt="MATCH_LINE")
        ev105 = load_json(pkg105 / "evidence/evidence.json")["evidence"][0]
        src105 = load_json(pkg105 / "source/source-index.json")["sources"][0]
        idx105 = PackageIndex()
        idx105.loaded_kinds.add("evidence")
        idx105.loaded_kinds.add("source")
        idx105.by_kind["evidence"] = {ev105["evidence_id"]: ev105}
        idx105.by_kind["source"] = {src105["source_id"]: src105}
        eid105 = ev105["evidence_id"]
        _c105, st105, snap105 = check_i12(idx105, pkg105, {eid105: "safe"})
        out105 = check_i14(idx105, pkg105, {eid105: "safe"}, st105, snap105)
        check("I14-T105 I12 pass", st105.get(eid105) == "pass")
        check("I14-T105 I14 PASS", out105.result == "PASS", out105.message)

        # I14-T106: snapshot mismatch → FAIL
        pkg106 = build_valid_minimal_package(root / "t106")
        _write_design(pkg106, "REAL_LINE\n")
        _patch_locator(pkg106, start=1, end=1, excerpt="NOT_IN_FILE")
        ev106 = load_json(pkg106 / "evidence/evidence.json")["evidence"][0]
        src106 = load_json(pkg106 / "source/source-index.json")["sources"][0]
        idx106 = PackageIndex()
        idx106.loaded_kinds.add("evidence")
        idx106.loaded_kinds.add("source")
        idx106.by_kind["evidence"] = {ev106["evidence_id"]: ev106}
        idx106.by_kind["source"] = {src106["source_id"]: src106}
        eid106 = ev106["evidence_id"]
        _c106, st106, snap106 = check_i12(idx106, pkg106, {eid106: "safe"})
        out106 = check_i14(idx106, pkg106, {eid106: "safe"}, st106, snap106)
        check("I14-T106 I12 pass", st106.get(eid106) == "pass")
        check("I14-T106 I14 FAIL", out106.result == "FAIL", out106.message)
        check(
            "I14-T106 excerpt_line_missing",
            "excerpt_line_missing" in out106.errors[0]["message"],
        )

        # I14-T107: mutate disk after I12 snapshot; I14 still uses snapshot
        pkg107 = build_valid_minimal_package(root / "t107")
        _write_design(pkg107, "ORIGINAL_SNAP\n")
        _patch_locator(pkg107, start=1, end=1, excerpt="ORIGINAL_SNAP")
        ev107 = load_json(pkg107 / "evidence/evidence.json")["evidence"][0]
        src107 = load_json(pkg107 / "source/source-index.json")["sources"][0]
        idx107 = PackageIndex()
        idx107.loaded_kinds.add("evidence")
        idx107.loaded_kinds.add("source")
        idx107.by_kind["evidence"] = {ev107["evidence_id"]: ev107}
        idx107.by_kind["source"] = {src107["source_id"]: src107}
        eid107 = ev107["evidence_id"]
        _c107, st107, snap107 = check_i12(idx107, pkg107, {eid107: "safe"})
        check("I14-T107 snapshot original", "ORIGINAL_SNAP" in snap107[eid107])
        _write_design(pkg107, "MUTATED_DISK\n")
        # Also change excerpt to match mutated disk — must still FAIL if using snapshot...
        # Keep excerpt as ORIGINAL_SNAP: disk no longer has it, snapshot does → PASS.
        reads107: list[str] = []

        def count107(self, *args, **kwargs):
            reads107.append(Path(self).name)
            return real_rt(self, *args, **kwargs)

        PathType.read_text = count107  # type: ignore[method-assign]
        try:
            out107 = check_i14(idx107, pkg107, {eid107: "safe"}, st107, snap107)
        finally:
            PathType.read_text = real_rt  # type: ignore[method-assign]
        check("I14-T107 I14 PASS on snapshot", out107.result == "PASS", out107.message)
        check("I14-T107 zero re-reads", reads107 == [], str(reads107))
        # Opposite: excerpt matches mutated disk only → still FAIL from snapshot
        ev107b = dict(ev107)
        loc107b = dict(ev107["locator"])
        loc107b["excerpt"] = "MUTATED_DISK"
        ev107b["locator"] = loc107b
        idx107b = PackageIndex()
        idx107b.loaded_kinds.add("evidence")
        idx107b.loaded_kinds.add("source")
        idx107b.by_kind["evidence"] = {eid107: ev107b}
        idx107b.by_kind["source"] = {src107["source_id"]: src107}
        out107b = check_i14(idx107b, pkg107, {eid107: "safe"}, st107, snap107)
        check("I14-T107 FAIL ignores disk mutate", out107b.result == "FAIL", out107b.message)


def _sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set_src_checksum(pkg: Path, source_id: str, checksum) -> None:
    doc = load_json(pkg / "source/source-index.json")
    for src in doc.get("sources", []):
        if src.get("source_id") == source_id:
            if checksum is None and "checksum" in src:
                del src["checksum"]
            elif checksum == "__null__":
                src["checksum"] = None
            else:
                src["checksum"] = checksum
            break
    save_json(pkg / "source/source-index.json", doc)


def _set_src_package_path(pkg: Path, source_id: str, package_path: str) -> None:
    doc = load_json(pkg / "source/source-index.json")
    for src in doc.get("sources", []):
        if src.get("source_id") == source_id:
            src["package_path"] = package_path
            break
    save_json(pkg / "source/source-index.json", doc)


def _i20_errors(report: dict) -> list[dict]:
    rm = result_map(report)
    return list(rm.get("I20", {}).get("errors") or [])


def _i20_msgs(report: dict) -> str:
    return " | ".join(e.get("message", "") for e in _i20_errors(report))


def test_c2_i20_checksum() -> None:
    """I20-T201..T222: package_copy SHA-256 via validate_package."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # --- T201: generated-output correct checksums ---
        pkg201 = root / "t201"
        shutil.copytree(GENERATED, pkg201)
        before201 = fingerprint_package(pkg201)
        report201 = validate_package(pkg201)
        after201 = fingerprint_package(pkg201)
        check("I20-T201 fingerprint unchanged", before201 == after201)
        expect_status(report201, "I20", "PASS", "I20-T201 generated PASS")
        check("I20-T201 L3 PASS", report201["layers"]["L3"] == "PASS")
        check(
            "I20-T201 final semantically_unreviewed",
            report201["final_status"] == "semantically_unreviewed",
            report201["final_status"],
        )

        # --- T202: wrong checksum → FAIL ---
        pkg202 = build_valid_minimal_package(root / "t202")
        digest202 = _sha256_hex(pkg202 / "source/original/design.md")
        wrong = ("0" if digest202[0] != "0" else "1") + digest202[1:]
        _set_src_checksum(
            pkg202,
            "src_001",
            {"alg": "sha256", "value": wrong, "of": "package_copy"},
        )
        before202 = fingerprint_package(pkg202)
        report202 = validate_package(pkg202)
        after202 = fingerprint_package(pkg202)
        check("I20-T202 fingerprint unchanged", before202 == after202)
        expect_status(report202, "I20", "FAIL", "I20-T202 mismatch FAIL")
        check("I20-T202 digest_mismatch", "digest_mismatch" in _i20_msgs(report202))

        # --- T203: uppercase hex matches ---
        pkg203 = build_valid_minimal_package(root / "t203")
        digest203 = _sha256_hex(pkg203 / "source/original/design.md")
        _set_src_checksum(
            pkg203,
            "src_001",
            {"alg": "sha256", "value": digest203.upper(), "of": "package_copy"},
        )
        expect_status(validate_package(pkg203), "I20", "PASS", "I20-T203 uppercase PASS")

        # --- T204: missing / null / empty → excluded → overall NOT_CHECKED ---
        pkg204a = build_valid_minimal_package(root / "t204a")
        expect_status(validate_package(pkg204a), "I20", "NOT_CHECKED", "I20-T204 missing")

        pkg204b = build_valid_minimal_package(root / "t204b")
        _set_src_checksum(pkg204b, "src_001", {"alg": "sha256", "value": None, "of": "package_copy"})
        report204b = validate_package(pkg204b)
        expect_status(report204b, "I20", "NOT_CHECKED", "I20-T204 value null")
        check("I20-T204 value_null reason", "value_null" in _i20_msgs(report204b))

        pkg204c = build_valid_minimal_package(root / "t204c")
        _set_src_checksum(pkg204c, "src_001", {"alg": "sha256", "value": "", "of": "package_copy"})
        report204c = validate_package(pkg204c)
        expect_status(report204c, "I20", "NOT_CHECKED", "I20-T204 value empty")
        check("I20-T204 value_empty reason", "value_empty" in _i20_msgs(report204c))

        # --- T205: malformed non-empty value ---
        pkg205 = build_valid_minimal_package(root / "t205")
        _set_src_checksum(
            pkg205,
            "src_001",
            {"alg": "sha256", "value": "not-a-hex-digest", "of": "package_copy"},
        )
        report205 = validate_package(pkg205)
        expect_status(report205, "I20", "NOT_CHECKED", "I20-T205 malformed NC")
        check("I20-T205 value_malformed", "value_malformed" in _i20_msgs(report205))

        # --- T206: unsupported alg ---
        pkg206 = build_valid_minimal_package(root / "t206")
        digest206 = _sha256_hex(pkg206 / "source/original/design.md")
        _set_src_checksum(
            pkg206,
            "src_001",
            {"alg": "SHA256", "value": digest206, "of": "package_copy"},
        )
        report206 = validate_package(pkg206)
        expect_status(report206, "I20", "NOT_CHECKED", "I20-T206 alg case NC")
        check("I20-T206 alg reason", "alg_unsupported_or_missing" in _i20_msgs(report206))

        pkg206b = build_valid_minimal_package(root / "t206b")
        _set_src_checksum(
            pkg206b,
            "src_001",
            {"alg": "md5", "value": digest206, "of": "package_copy"},
        )
        expect_status(validate_package(pkg206b), "I20", "NOT_CHECKED", "I20-T206 md5 NC")

        # --- T207: missing/other of ---
        pkg207 = build_valid_minimal_package(root / "t207")
        _set_src_checksum(
            pkg207,
            "src_001",
            {"alg": "sha256", "value": digest206, "of": "original"},
        )
        report207 = validate_package(pkg207)
        expect_status(report207, "I20", "NOT_CHECKED", "I20-T207 of NC")
        check("I20-T207 of reason", "of_unsupported_or_missing" in _i20_msgs(report207))

        pkg207b = build_valid_minimal_package(root / "t207b")
        _set_src_checksum(
            pkg207b,
            "src_001",
            {"alg": "sha256", "value": digest206},
        )
        expect_status(validate_package(pkg207b), "I20", "NOT_CHECKED", "I20-T207 missing of")

        # --- T208: normal relative path + correct hash ---
        pkg208 = build_valid_minimal_package(root / "t208")
        digest208 = _sha256_hex(pkg208 / "source/original/design.md")
        _set_src_checksum(
            pkg208,
            "src_001",
            {"alg": "sha256", "value": digest208, "of": "package_copy"},
        )
        report208 = validate_package(pkg208)
        expect_status(report208, "I20", "PASS", "I20-T208 normal PASS")
        # I10–I16 regression on same package
        for iid in ["I10", "I11", "I12", "I13", "I14", "I16"]:
            expect_status(report208, iid, "PASS", f"I20-T222 regress {iid}")

        # --- T209: escaping path + zero content read of outside file ---
        pkg209 = build_valid_minimal_package(root / "t209")
        outside209 = root / "outside209.txt"
        outside209.write_text("OUTSIDE-SECRET-209\n", encoding="utf-8")
        digest209 = _sha256_hex(pkg209 / "source/original/design.md")
        _set_src_checksum(
            pkg209,
            "src_001",
            {"alg": "sha256", "value": digest209, "of": "package_copy"},
        )
        _set_src_package_path(pkg209, "src_001", "../outside209.txt")
        before_o209 = outside209.read_text(encoding="utf-8")
        opened209: list[str] = []
        real_open209 = Path.open

        def counting_open209(self, *args, **kwargs):
            try:
                if self.resolve() == outside209.resolve():
                    opened209.append(self.as_posix())
            except OSError:
                opened209.append("unresolvable")
            return real_open209(self, *args, **kwargs)

        Path.open = counting_open209  # type: ignore[method-assign]
        try:
            report209 = validate_package(pkg209)
        finally:
            Path.open = real_open209  # type: ignore[method-assign]
        after_o209 = outside209.read_text(encoding="utf-8")
        expect_status(report209, "I20", "NOT_CHECKED", "I20-T209 escape NC")
        check("I20-T209 zero outside open", opened209 == [], str(opened209))
        check("I20-T209 outside unchanged", before_o209 == after_o209)

        # --- T210: internal symlink to regular file ---
        pkg210 = build_valid_minimal_package(root / "t210")
        target210 = pkg210 / "source/original/design.md"
        link210 = pkg210 / "source/original/design-link.md"
        digest210 = _sha256_hex(target210)
        try:
            link210.symlink_to(target210.name)
            _set_src_package_path(pkg210, "src_001", "source/original/design-link.md")
            _set_src_checksum(
                pkg210,
                "src_001",
                {"alg": "sha256", "value": digest210, "of": "package_copy"},
            )
            expect_status(validate_package(pkg210), "I20", "PASS", "I20-T210 internal symlink PASS")
        except OSError:
            check("I20-T210 symlink SKIPPED (host)", True)

        # --- T211: symlink escaping package ---
        pkg211 = build_valid_minimal_package(root / "t211")
        outside211 = root / "outside211.txt"
        outside211.write_text("OUTSIDE-SECRET-211\n", encoding="utf-8")
        link211 = pkg211 / "source/original/escape-link.md"
        digest211 = _sha256_hex(pkg211 / "source/original/design.md")
        try:
            link211.symlink_to(outside211)
            _set_src_package_path(pkg211, "src_001", "source/original/escape-link.md")
            _set_src_checksum(
                pkg211,
                "src_001",
                {"alg": "sha256", "value": digest211, "of": "package_copy"},
            )
            opened211: list[str] = []
            real_open211 = Path.open

            def counting_open211(self, *args, **kwargs):
                try:
                    if self.resolve() == outside211.resolve():
                        opened211.append(self.as_posix())
                except OSError:
                    opened211.append("unresolvable")
                return real_open211(self, *args, **kwargs)

            Path.open = counting_open211  # type: ignore[method-assign]
            try:
                report211 = validate_package(pkg211)
            finally:
                Path.open = real_open211  # type: ignore[method-assign]
            expect_status(report211, "I20", "NOT_CHECKED", "I20-T211 escape symlink NC")
            check("I20-T211 zero outside open", opened211 == [], str(opened211))
        except OSError:
            check("I20-T211 symlink SKIPPED (host)", True)

        # --- T212: missing file ---
        pkg212 = build_valid_minimal_package(root / "t212")
        _set_src_package_path(pkg212, "src_001", "source/original/missing-copy.md")
        _set_src_checksum(
            pkg212,
            "src_001",
            {
                "alg": "sha256",
                "value": "a" * 64,
                "of": "package_copy",
            },
        )
        report212 = validate_package(pkg212)
        expect_status(report212, "I20", "NOT_CHECKED", "I20-T212 missing NC")
        check(
            "I20-T212 missing reason",
            "package_copy_missing" in _i20_msgs(report212)
            or "path_escapes" in _i20_msgs(report212)
            or "not checked" in _i20_msgs(report212),
        )

        # --- T213: directory target ---
        pkg213 = build_valid_minimal_package(root / "t213")
        _set_src_package_path(pkg213, "src_001", "source/original")
        _set_src_checksum(
            pkg213,
            "src_001",
            {"alg": "sha256", "value": "b" * 64, "of": "package_copy"},
        )
        report213 = validate_package(pkg213)
        expect_status(report213, "I20", "NOT_CHECKED", "I20-T213 dir NC")
        check("I20-T213 not_file", "package_copy_not_file" in _i20_msgs(report213))

        # --- T214: read failure (patch I20 hasher only; keep L1 fingerprint intact) ---
        import _integrity as _integrity_mod

        pkg214 = build_valid_minimal_package(root / "t214")
        design214 = pkg214 / "source/original/design.md"
        digest214 = _sha256_hex(design214)
        _set_src_checksum(
            pkg214,
            "src_001",
            {"alg": "sha256", "value": digest214, "of": "package_copy"},
        )
        real_sha214 = _integrity_mod._sha256_file

        def boom_sha214(path: Path) -> str:
            try:
                if path.resolve() == design214.resolve():
                    raise OSError("simulated I20 read failure")
            except OSError as exc:
                if "simulated" in str(exc):
                    raise
            return real_sha214(path)

        _integrity_mod._sha256_file = boom_sha214  # type: ignore[assignment]
        try:
            report214 = validate_package(pkg214)
        finally:
            _integrity_mod._sha256_file = real_sha214  # type: ignore[assignment]
        expect_status(report214, "I20", "NOT_CHECKED", "I20-T214 read_failed NC")
        check("I20-T214 read_failed reason", "read_failed" in _i20_msgs(report214))

        # --- T215: multi-source FAIL + PASS → overall FAIL ---
        pkg215 = build_valid_minimal_package(root / "t215")
        design215 = pkg215 / "source/original/design.md"
        extra215 = pkg215 / "source/original/extra.md"
        extra215.write_text("extra line\n", encoding="utf-8")
        dig_ok = _sha256_hex(design215)
        dig_extra = _sha256_hex(extra215)
        doc215 = load_json(pkg215 / "source/source-index.json")
        doc215["sources"].append(
            {
                "source_id": "src_002",
                "original_name": "extra.md",
                "user_path": None,
                "package_path": "source/original/extra.md",
                "media_type": "text/markdown",
                "language": "zh",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": None,
                "readable": True,
                "notes": "",
                "checksum": {
                    "alg": "sha256",
                    "value": dig_extra,
                    "of": "package_copy",
                },
            }
        )
        doc215["sources"][0]["checksum"] = {
            "alg": "sha256",
            "value": ("0" if dig_ok[0] != "0" else "1") + dig_ok[1:],
            "of": "package_copy",
        }
        save_json(pkg215 / "source/source-index.json", doc215)
        # Keep manifest sources_summary permissive; schema may not enforce count match.
        report215 = validate_package(pkg215)
        expect_status(report215, "I20", "FAIL", "I20-T215 multi FAIL")
        msgs215 = _i20_msgs(report215)
        check("I20-T215 has mismatch", "digest_mismatch" in msgs215)
        check("I20-T215 keeps both sources", "src_001" in msgs215)

        # --- T216: two sources same path — cache (open once for content hash) ---
        pkg216 = build_valid_minimal_package(root / "t216")
        design216 = pkg216 / "source/original/design.md"
        dig216 = _sha256_hex(design216)
        doc216 = load_json(pkg216 / "source/source-index.json")
        doc216["sources"][0]["checksum"] = {
            "alg": "sha256",
            "value": dig216,
            "of": "package_copy",
        }
        doc216["sources"].append(
            {
                "source_id": "src_002",
                "original_name": "design.md",
                "user_path": None,
                "package_path": "source/original/design.md",
                "media_type": "text/markdown",
                "language": "zh",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": None,
                "readable": True,
                "notes": "",
                "checksum": {
                    "alg": "sha256",
                    "value": dig216,
                    "of": "package_copy",
                },
            }
        )
        save_json(pkg216 / "source/source-index.json", doc216)
        hash_calls216: list[str] = []
        import _integrity as _integrity_mod216

        real_sha216 = _integrity_mod216._sha256_file

        def counting_sha216(path: Path) -> str:
            hash_calls216.append(path.resolve().as_posix())
            return real_sha216(path)

        _integrity_mod216._sha256_file = counting_sha216  # type: ignore[assignment]
        try:
            report216 = validate_package(pkg216)
        finally:
            _integrity_mod216._sha256_file = real_sha216  # type: ignore[assignment]
        expect_status(report216, "I20", "PASS", "I20-T216 same path PASS")
        check(
            "I20-T216 message two matches",
            "all 2 applicable" in result_map(report216)["I20"]["message"],
            result_map(report216)["I20"]["message"],
        )
        check(
            "I20-T216 digest cached once",
            len(hash_calls216) == 1,
            str(hash_calls216),
        )

        # --- T217: zero applicable (explicit empty checksum object missing value) ---
        pkg217 = build_valid_minimal_package(root / "t217")
        _set_src_checksum(pkg217, "src_001", {"alg": "sha256", "of": "package_copy"})
        report217 = validate_package(pkg217)
        expect_status(report217, "I20", "NOT_CHECKED", "I20-T217 zero applicable")
        check(
            "I20-T217 message zero",
            "zero applicable" in result_map(report217)["I20"]["message"],
        )

        # --- T218: excluded + PASS → overall PASS ---
        pkg218 = build_valid_minimal_package(root / "t218")
        design218 = pkg218 / "source/original/design.md"
        extra218 = pkg218 / "source/original/extra218.md"
        extra218.write_text("ok\n", encoding="utf-8")
        dig218 = _sha256_hex(design218)
        dig218e = _sha256_hex(extra218)
        doc218 = load_json(pkg218 / "source/source-index.json")
        doc218["sources"][0]["checksum"] = {
            "alg": "sha256",
            "value": dig218,
            "of": "package_copy",
        }
        doc218["sources"].append(
            {
                "source_id": "src_002",
                "original_name": "extra218.md",
                "user_path": None,
                "package_path": "source/original/extra218.md",
                "media_type": "text/markdown",
                "language": "zh",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": None,
                "readable": True,
                "notes": "",
            }
        )
        save_json(pkg218 / "source/source-index.json", doc218)
        report218 = validate_package(pkg218)
        expect_status(report218, "I20", "PASS", "I20-T218 excluded+PASS → PASS")
        check("I20-T218 excluded detail", "src_002" in _i20_msgs(report218))
        # silence unused
        check("I20-T218 digests computed", dig218e != "")

        # --- T219: excluded + shape NC → overall NOT_CHECKED ---
        pkg219 = build_valid_minimal_package(root / "t219")
        doc219 = load_json(pkg219 / "source/source-index.json")
        doc219["sources"][0]["checksum"] = {
            "alg": "sha256",
            "value": "deadbeef",
            "of": "package_copy",
        }
        doc219["sources"].append(
            {
                "source_id": "src_002",
                "original_name": "x.md",
                "user_path": None,
                "package_path": "source/original/design.md",
                "media_type": "text/markdown",
                "language": "zh",
                "role": "supporting",
                "received_from": "user",
                "content_transformed": None,
                "readable": True,
                "notes": "",
            }
        )
        save_json(pkg219 / "source/source-index.json", doc219)
        expect_status(validate_package(pkg219), "I20", "NOT_CHECKED", "I20-T219 excluded+NC")

        # --- T220: minimal no checksum (already covered) + fingerprint ---
        pkg220 = build_valid_minimal_package(root / "t220")
        before220 = fingerprint_package(pkg220)
        report220 = validate_package(pkg220)
        after220 = fingerprint_package(pkg220)
        expect_status(report220, "I20", "NOT_CHECKED", "I20-T220 minimal NC")
        check("I20-T220 fingerprint", before220 == after220)

        # --- T221: source-index not loaded (S03 fail via bad JSON shape kept parseable but schema fail) ---
        pkg221 = build_valid_minimal_package(root / "t221")
        # Break schema: remove required field media_type
        doc221 = load_json(pkg221 / "source/source-index.json")
        del doc221["sources"][0]["media_type"]
        save_json(pkg221 / "source/source-index.json", doc221)
        report221 = validate_package(pkg221)
        expect_status(report221, "S03", "FAIL", "I20-T221 S03 FAIL")
        expect_status(report221, "I20", "NOT_CHECKED", "I20-T221 source unloaded")
        check(
            "I20-T221 message",
            "source-index not loaded" in result_map(report221)["I20"]["message"],
        )


def main() -> int:
    print("== context-validator L3-A + B1–B4 + C1 (I14) + C2 (I20) tests ==")
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
    test_convergence_i18_privacy_and_whitespace()
    test_convergence_i01_partial_with_duplicate()
    test_convergence_mid_dir_symlink()
    test_convergence_l3_warning_vs_not_checked()
    test_b1_i11_i10_paths()
    test_b2_i16_readable_false()
    test_b3_i12_line_range()
    test_b4_i13_other_locators()
    test_c1_i14_excerpt_match()
    test_c2_i20_checksum()
    test_report_and_offline()

    print(f"\nSummary: {PASSES} passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
