#!/usr/bin/env python3
"""Tests for context-validator L3-A + L3-B1 (I11/I10) + L3-B2 (I16)."""

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
L3_B1 = ["I10", "I11"]
L3_B2 = ["I16"]
L3_DEFERRED = ["I12", "I13", "I14", "I20"]


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
        for iid in L3_B1:
            expect_status(report, iid, "PASS", f"generated {iid}")
        for iid in L3_B2:
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
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B1:
            expect_status(report, iid, "PASS", f"empty {iid}")
        for iid in L3_B2:
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
        expect_status(report_m, "I10", "PASS", "minimal I10")
        expect_status(report_m, "I11", "PASS", "minimal I11")
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
            "L3 layer not full PASS with deferred I*",
            report["layers"]["L3"] == "NOT_CHECKED",
            report["layers"]["L3"],
        )
        check("L1 unchanged style", report["layers"]["L1"] in {"PASS", "WARNING"})
        check("L2 PASS", report["layers"]["L2"] == "PASS")
        # Per-check deferred still NOT_CHECKED; A rules still individual PASS
        expect_status(report, "I01", "PASS", "layer mix I01 PASS")
        expect_status(report, "I14", "NOT_CHECKED", "layer mix I14 NOT_CHECKED")


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
    """I19 WARNING must not make L3 layer look finished while B/C remain NOT_CHECKED."""
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
        expect_status(report, "I14", "NOT_CHECKED", "warn-layer I14 NOT_CHECKED")
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
            check("phase 3B-B2", report["checker"]["phase"] == "3B-B2")
            check("L3-A flag", report["checker"]["scripts_implemented"]["L3_A_references"] is True)
            check(
                "L3-B1 flag",
                report["checker"]["scripts_implemented"]["L3_B1_path_safety_exists"] is True,
            )
            check(
                "L3-B2 flag",
                report["checker"]["scripts_implemented"]["L3_B2_readable_false"] is True,
            )
            check("L3-B full locators false", report["checker"]["scripts_implemented"]["L3_B_locators"] is False)
            check("read_only", report["read_only"] is True)
            ids = {c["id"] for c in report["checks"]}
            for iid in L3A + L3_B1 + L3_B2 + L3_DEFERRED:
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


def main() -> int:
    print("== context-validator L3-A + L3-B1 + L3-B2 tests ==")
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
    test_report_and_offline()

    print(f"\nSummary: {PASSES} passed, {len(FAILURES)} failed")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
