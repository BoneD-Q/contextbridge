#!/usr/bin/env python3
"""CBHF 0.1.0 deterministic validation helper for context-validator.

Skills-first: this script is invoked by the Skill; it is not a product CLI.
Phase 3B: L1 + L2 + L3-A + L3-B1 (I11/I10) + L3-B2 (I16 readable:false).
Remaining L3-B/C (I12/I13/I14/I20) and L4 remain NOT_CHECKED.
Never writes into the package. Never fetches schemas from the network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from _integrity import run_l3_batch_a

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_SCHEMA_DIR = REPO_ROOT / "spec" / "cbhf" / "v0.1.0"

REQUIRED_PATHS = [
    "manifest.yaml",
    "source/source-index.json",
    "source/original",
    "knowledge/overview.md",
    "knowledge/facts.json",
    "knowledge/claims.json",
    "knowledge/decisions.json",
    "knowledge/constraints.json",
    "knowledge/glossary.json",
    "evidence/evidence.json",
    "evidence/references.json",
    "uncertainty/unknowns.json",
    "uncertainty/conflicts.json",
    "handoff/receiver-guide.md",
    "handoff/questions.json",
    "handoff/recommended-actions.json",
]

REQUIRED_JSON_FILES = [
    "source/source-index.json",
    "knowledge/facts.json",
    "knowledge/claims.json",
    "knowledge/decisions.json",
    "knowledge/constraints.json",
    "knowledge/glossary.json",
    "evidence/evidence.json",
    "evidence/references.json",
    "uncertainty/unknowns.json",
    "uncertainty/conflicts.json",
    "handoff/questions.json",
    "handoff/recommended-actions.json",
]

# Known top-level names (Open Question Q1: unknowns → WARNING, not FAIL).
ALLOWED_TOP_LEVEL = {
    "manifest.yaml",
    "source",
    "knowledge",
    "evidence",
    "uncertainty",
    "handoff",
    "validation",  # Validator-owned optional; Phase 2 does not create it
}

SCHEMA_FILES = [
    "common.schema.json",
    "manifest.schema.json",
    "source.schema.json",
    "claim.schema.json",
    "fact.schema.json",
    "decision.schema.json",
    "constraint.schema.json",
    "glossary.schema.json",
    "evidence.schema.json",
    "unknown.schema.json",
    "conflict.schema.json",
    "questions.schema.json",
    "recommended-actions.schema.json",
]

# check_id -> (relative_path, schema_file, fragment_or_None)
SCHEMA_TARGETS: dict[str, tuple[str, str, str | None]] = {
    "S02": ("manifest.yaml", "manifest.schema.json", None),
    "S03": ("source/source-index.json", "source.schema.json", None),
    "S04": ("knowledge/facts.json", "fact.schema.json", None),
    "S05": ("knowledge/claims.json", "claim.schema.json", None),
    "S06": ("knowledge/decisions.json", "decision.schema.json", None),
    "S07": ("knowledge/constraints.json", "constraint.schema.json", None),
    "S08": ("knowledge/glossary.json", "glossary.schema.json", None),
    "S09": ("evidence/evidence.json", "evidence.schema.json", None),
    "S10": (
        "evidence/references.json",
        "evidence.schema.json",
        "#/$defs/ReferencesDocument",
    ),
    "S11": ("uncertainty/unknowns.json", "unknown.schema.json", None),
    "S12": ("uncertainty/conflicts.json", "conflict.schema.json", None),
    "S13": ("handoff/questions.json", "questions.schema.json", None),
    "S14": (
        "handoff/recommended-actions.json",
        "recommended-actions.schema.json",
        None,
    ),
}

L4_CHECK_IDS = [f"H{i:02d}" for i in range(1, 7)]

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARNING = "WARNING"
STATUS_NOT_CHECKED = "NOT_CHECKED"
STATUS_NEEDS_HUMAN = "NEEDS_HUMAN_REVIEW"


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently overwriting."""


def _construct_mapping_no_duplicates(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key: {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


class DuplicateKeyError(ValueError):
    pass


def _object_pairs_hook_no_duplicates(pairs: list[tuple[Any, Any]]) -> dict:
    out: dict[Any, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError(f"duplicate key: {key!r}")
        out[key] = value
    return out


def load_json_reject_duplicates(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_object_pairs_hook_no_duplicates)


def load_yaml_unique(text: str) -> Any:
    return yaml.load(text, Loader=UniqueKeyLoader)


@dataclass
class CheckResult:
    id: str
    name: str
    result: str
    message: str = ""
    path: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "result": self.result,
            "message": self.message,
        }
        if self.path is not None:
            d["path"] = self.path
        if self.errors:
            d["errors"] = self.errors
        return d


def privacy_label(package: Path) -> str:
    return package.name or "package"


def safe_rel(package: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(package.resolve()).as_posix()
    except ValueError:
        return path.name


def iter_package_files(package: Path) -> list[Path]:
    """List regular files under package without following directory symlinks."""
    files: list[Path] = []
    root = package.resolve()
    for dirpath, dirnames, filenames in os.walk(package, followlinks=False):
        current = Path(dirpath)
        # Drop dirnames that escape package root via symlink
        keep: list[str] = []
        for name in dirnames:
            child = current / name
            try:
                if child.is_symlink():
                    # Do not descend into symlinked directories (path-escape safety).
                    continue
                resolved = child.resolve()
                resolved.relative_to(root)
                keep.append(name)
            except (ValueError, OSError):
                continue
        dirnames[:] = keep
        for name in filenames:
            fp = current / name
            if fp.is_symlink():
                # Record presence for hashing/P03 only if target stays inside root.
                try:
                    target = fp.resolve()
                    target.relative_to(root)
                except (ValueError, OSError):
                    continue
            files.append(fp)
    return sorted(files, key=lambda p: p.as_posix())


def fingerprint_package(package: Path) -> dict[str, str]:
    """Map package-relative posix path -> sha256 of file bytes."""
    digests: dict[str, str] = {}
    root = package.resolve()
    for fp in iter_package_files(package):
        try:
            rel = fp.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        h = hashlib.sha256()
        with fp.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        digests[rel] = h.hexdigest()
    return digests


def layer_status(
    results: list[CheckResult],
    *,
    mixed_pass_not_checked: str = STATUS_PASS,
    prefer_incomplete_over_warning: bool = False,
) -> str:
    """Roll up a layer.

    L1/L2: WARNING outranks; mixed PASS+NOT_CHECKED → PASS (default).
    L3: pass mixed_pass_not_checked=NOT_CHECKED and
    prefer_incomplete_over_warning=True so deferred I* keep the layer from
    looking finished when only an executed check warned (e.g. I19).
    Per-check WARNING rows remain in report.warnings; final_status unchanged.
    """
    statuses = {r.result for r in results}
    if STATUS_FAIL in statuses:
        return STATUS_FAIL
    # L3 incompleteness before WARNING — layer must not read as "done with warnings".
    if prefer_incomplete_over_warning and STATUS_NOT_CHECKED in statuses:
        return STATUS_NOT_CHECKED
    if STATUS_WARNING in statuses:
        return STATUS_WARNING
    if statuses and statuses <= {STATUS_PASS}:
        return STATUS_PASS
    if STATUS_NEEDS_HUMAN in statuses and STATUS_PASS not in statuses and STATUS_FAIL not in statuses:
        # L4-only layer
        if statuses <= {STATUS_NEEDS_HUMAN, STATUS_NOT_CHECKED}:
            return STATUS_NOT_CHECKED if STATUS_NOT_CHECKED in statuses and STATUS_NEEDS_HUMAN not in statuses else (
                STATUS_NEEDS_HUMAN if STATUS_NEEDS_HUMAN in statuses else STATUS_NOT_CHECKED
            )
    if STATUS_NOT_CHECKED in statuses and STATUS_PASS not in statuses and STATUS_FAIL not in statuses and STATUS_WARNING not in statuses:
        return STATUS_NOT_CHECKED
    if STATUS_PASS in statuses and STATUS_NOT_CHECKED in statuses:
        return mixed_pass_not_checked
    return STATUS_NOT_CHECKED


def package_final_status(
    checks: list[CheckResult],
    *,
    l3_implemented: bool,
    l4_reviewed: bool,
) -> str:
    """Roll up package status per report-format.md (not per-check codes)."""
    executed_structural = [
        c for c in checks if c.id.startswith(("P", "S")) and c.result != STATUS_NOT_CHECKED
    ]
    if any(c.result == STATUS_FAIL for c in checks if c.id.startswith(("P", "S", "I"))):
        return "invalid"

    important_not_checked = [
        c
        for c in checks
        if c.id.startswith(("P", "S")) and c.result == STATUS_NOT_CHECKED
    ]
    # Phase 2: entire L3 intentionally NOT_CHECKED → not fully validated.
    if not l3_implemented or any(c.id.startswith("I") and c.result == STATUS_NOT_CHECKED for c in checks):
        if important_not_checked:
            return "not_fully_validated"
        # L1/L2 ran; L3 deferred
        if any(c.result == STATUS_WARNING for c in executed_structural):
            # Prefer honesty that L3 is missing over warning-only label when L3 absent.
            return "not_fully_validated"
        return "not_fully_validated"

    if any(c.result == STATUS_WARNING for c in checks if c.id.startswith(("P", "S", "I"))):
        return "structurally_valid_with_warnings"
    if not l4_reviewed:
        return "semantically_unreviewed"
    return "structurally_valid"


def pointer_from_error(err) -> str:
    parts = list(err.absolute_path)
    if not parts:
        return ""
    out = ""
    for p in parts:
        if isinstance(p, int):
            out += f"/{p}"
        else:
            out += f"/{p}"
    return out


def build_registry(schema_dir: Path) -> tuple[Registry | None, list[str], dict[str, Any]]:
    """Load local schemas only. Returns (registry, errors, schemas_by_name)."""
    errors: list[str] = []
    schemas: dict[str, Any] = {}
    registry: Registry = Registry()
    if not schema_dir.is_dir():
        return None, [f"schema directory missing: {schema_dir.name}"], {}

    for name in SCHEMA_FILES:
        path = schema_dir / name
        if not path.is_file():
            errors.append(f"missing schema file: {name}")
            continue
        try:
            data = load_json_reject_duplicates(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(data)
            schemas[name] = data
            resource = Resource.from_contents(data, default_specification=DRAFT202012)
            registry = registry.with_resource(data["$id"], resource)
            registry = registry.with_resource(name, resource)
        except (OSError, DuplicateKeyError, json.JSONDecodeError, SchemaError, KeyError) as exc:
            errors.append(f"{name}: {exc}")

    if errors:
        return None, errors, schemas
    return registry, [], schemas


def validate_package(
    package: Path,
    *,
    schema_dir: Path | None = None,
) -> dict[str, Any]:
    schema_dir = schema_dir or DEFAULT_SCHEMA_DIR
    package = package.resolve()
    validated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    checks: list[CheckResult] = []
    parsed_objects: dict[str, Any] = {}
    parse_ok: dict[str, bool] = {}
    limitations: list[str] = [
        "Phase 3B Batch B2: L1 + L2 + L3-A + I11/I10 + I16.",
        "Still NOT_CHECKED: I12, I13, I14, I20, and L4.",
        "L3 PASS is not semantic adequacy; I14 not implemented.",
        "Report is session-level; package was not modified.",
        "Schemas loaded from local spec/cbhf/v0.1.0 only (no network).",
    ]

    if not package.is_dir():
        checks.append(
            CheckResult(
                "P01",
                "Required paths exist",
                STATUS_FAIL,
                "package root is not a directory",
                path=".",
            )
        )
        return _finalize_report(
            package=package,
            validated_at=validated_at,
            checks=checks,
            cbhf_version=None,
            package_id=None,
            limitations=limitations,
            fingerprint_before={},
            fingerprint_after={},
        )

    fingerprint_before = fingerprint_package(package)

    # --- P01 ---
    missing = [rel for rel in REQUIRED_PATHS if not (package / rel).exists()]
    if missing:
        checks.append(
            CheckResult(
                "P01",
                "Required paths exist",
                STATUS_FAIL,
                f"missing {len(missing)} required path(s)",
                path=".",
                errors=[{"path": m, "message": "missing"} for m in missing],
            )
        )
    else:
        checks.append(
            CheckResult("P01", "Required paths exist", STATUS_PASS, "all required paths present")
        )

    # --- P02 ---
    md_files = ["knowledge/overview.md", "handoff/receiver-guide.md"]
    md_errors: list[dict[str, str]] = []
    for rel in md_files:
        path = package / rel
        if not path.is_file():
            md_errors.append({"path": rel, "message": "missing or not a file"})
            continue
        try:
            path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            md_errors.append({"path": rel, "message": str(exc)})
    if md_errors:
        # If missing because P01 failed, still FAIL (readable check failed).
        checks.append(
            CheckResult(
                "P02",
                "Markdown readable",
                STATUS_FAIL,
                "one or more markdown files unreadable",
                errors=md_errors,
            )
        )
    else:
        checks.append(
            CheckResult("P02", "Markdown readable", STATUS_PASS, "overview and receiver-guide readable as UTF-8")
        )

    # --- P03 JSON parse (reject duplicates) ---
    json_errors: list[dict[str, str]] = []
    json_paths: list[Path] = []
    for fp in iter_package_files(package):
        if fp.suffix.lower() == ".json":
            json_paths.append(fp)

    for fp in json_paths:
        rel = safe_rel(package, fp)
        try:
            text = fp.read_text(encoding="utf-8")
            obj = load_json_reject_duplicates(text)
            parsed_objects[rel] = obj
            parse_ok[rel] = True
        except DuplicateKeyError as exc:
            parse_ok[rel] = False
            json_errors.append({"path": rel, "message": str(exc)})
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            parse_ok[rel] = False
            json_errors.append({"path": rel, "message": str(exc)})

    # Ensure required JSON files that were missing are counted
    for rel in REQUIRED_JSON_FILES:
        if rel not in parse_ok and not (package / rel).is_file():
            parse_ok[rel] = False
            if not any(e["path"] == rel for e in json_errors):
                json_errors.append({"path": rel, "message": "missing file"})

    if json_errors:
        checks.append(
            CheckResult(
                "P03",
                "JSON parseable (reject duplicate keys)",
                STATUS_FAIL,
                f"{len(json_errors)} JSON file(s) failed parse/duplicate-key check",
                errors=json_errors,
            )
        )
    else:
        checks.append(
            CheckResult(
                "P03",
                "JSON parseable (reject duplicate keys)",
                STATUS_PASS,
                f"parsed {len(json_paths)} JSON file(s) with duplicate-key rejection",
            )
        )

    # --- P04 YAML ---
    manifest_rel = "manifest.yaml"
    manifest_obj = None
    yaml_path = package / manifest_rel
    if not yaml_path.is_file():
        checks.append(
            CheckResult(
                "P04",
                "YAML parseable (reject duplicate keys)",
                STATUS_FAIL,
                "manifest.yaml missing",
                path=manifest_rel,
            )
        )
        parse_ok[manifest_rel] = False
    else:
        try:
            manifest_obj = load_yaml_unique(yaml_path.read_text(encoding="utf-8"))
            parsed_objects[manifest_rel] = manifest_obj
            parse_ok[manifest_rel] = True
            checks.append(
                CheckResult(
                    "P04",
                    "YAML parseable (reject duplicate keys)",
                    STATUS_PASS,
                    "manifest.yaml parsed with unique-key loader",
                    path=manifest_rel,
                )
            )
        except yaml.YAMLError as exc:
            parse_ok[manifest_rel] = False
            checks.append(
                CheckResult(
                    "P04",
                    "YAML parseable (reject duplicate keys)",
                    STATUS_FAIL,
                    str(exc).strip(),
                    path=manifest_rel,
                )
            )

    # --- P05 package form ---
    if not parse_ok.get(manifest_rel):
        checks.append(
            CheckResult(
                "P05",
                "Package form",
                STATUS_NOT_CHECKED,
                "manifest unreadable; cannot confirm package_form/scenario",
                path=manifest_rel,
            )
        )
    else:
        form = manifest_obj.get("package_form") if isinstance(manifest_obj, dict) else None
        scenario = manifest_obj.get("scenario") if isinstance(manifest_obj, dict) else None
        layout_ok = (package / "source").is_dir() and (package / "knowledge").is_dir()
        if form == "folder" and scenario == "docs" and layout_ok:
            checks.append(
                CheckResult(
                    "P05",
                    "Package form",
                    STATUS_PASS,
                    "folder/docs package layout consistent",
                    path=manifest_rel,
                )
            )
        else:
            checks.append(
                CheckResult(
                    "P05",
                    "Package form",
                    STATUS_FAIL,
                    f"expected package_form=folder scenario=docs with folder layout; "
                    f"got package_form={form!r} scenario={scenario!r} layout_ok={layout_ok}",
                    path=manifest_rel,
                )
            )

    # --- P06 extra top-level (WARNING only; Q1) ---
    try:
        top = sorted(p.name for p in package.iterdir())
        extras = [name for name in top if name not in ALLOWED_TOP_LEVEL]
        if extras:
            checks.append(
                CheckResult(
                    "P06",
                    "Extra / unexpected entries",
                    STATUS_WARNING,
                    "unexpected top-level entries (Open Question Q1: warn, not fail)",
                    errors=[{"path": name, "message": "unexpected top-level"} for name in extras],
                )
            )
        else:
            checks.append(
                CheckResult(
                    "P06",
                    "Extra / unexpected entries",
                    STATUS_PASS,
                    "no unexpected top-level entries",
                )
            )
    except OSError as exc:
        checks.append(
            CheckResult(
                "P06",
                "Extra / unexpected entries",
                STATUS_NOT_CHECKED,
                f"cannot enumerate package root: {exc}",
            )
        )

    # --- L2 S01 load schemas ---
    registry, schema_load_errors, schemas_by_name = build_registry(schema_dir)
    if schema_load_errors:
        checks.append(
            CheckResult(
                "S01",
                "Load schemas",
                STATUS_FAIL,
                "one or more local schemas failed to load",
                path=schema_dir.name,
                errors=[{"path": e.split(":")[0], "message": e} for e in schema_load_errors],
            )
        )
    else:
        checks.append(
            CheckResult(
                "S01",
                "Load schemas",
                STATUS_PASS,
                f"loaded {len(SCHEMA_FILES)} Draft 2020-12 schemas from local disk",
                path="spec/cbhf/v0.1.0",
            )
        )

    schema_keyword_failures: list[dict[str, str]] = []

    def run_schema_check(
        check_id: str,
        name: str,
        rel: str,
        schema_name: str,
        fragment: str | None,
    ) -> CheckResult:
        if registry is None or schema_load_errors:
            return CheckResult(
                check_id,
                name,
                STATUS_NOT_CHECKED,
                "schemas unavailable (S01 failed)",
                path=rel,
            )
        if not parse_ok.get(rel):
            return CheckResult(
                check_id,
                name,
                STATUS_NOT_CHECKED,
                "instance not parseable in L1; schema not run",
                path=rel,
            )
        instance = parsed_objects.get(rel)
        schema = schemas_by_name.get(schema_name)
        if schema is None:
            return CheckResult(
                check_id,
                name,
                STATUS_NOT_CHECKED,
                f"schema {schema_name} not loaded",
                path=rel,
            )
        if fragment:
            wrapped = {"$ref": f"{schema['$id']}{fragment}"}
            validator = Draft202012Validator(wrapped, registry=registry)
        else:
            validator = Draft202012Validator(schema, registry=registry)
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
        if errors:
            err_dicts = []
            for e in errors[:20]:
                ptr = pointer_from_error(e)
                err_dicts.append(
                    {
                        "path": f"{rel}#{ptr}" if ptr else rel,
                        "message": e.message,
                    }
                )
                schema_keyword_failures.append(err_dicts[-1])
            return CheckResult(
                check_id,
                name,
                STATUS_FAIL,
                f"{len(errors)} schema error(s)",
                path=rel,
                errors=err_dicts,
            )
        return CheckResult(check_id, name, STATUS_PASS, "schema valid", path=rel)

    schema_names = {
        "S02": "manifest schema",
        "S03": "source-index schema",
        "S04": "facts schema",
        "S05": "claims schema",
        "S06": "decisions schema",
        "S07": "constraints schema",
        "S08": "glossary schema",
        "S09": "evidence schema",
        "S10": "references schema",
        "S11": "unknowns schema",
        "S12": "conflicts schema",
        "S13": "questions schema",
        "S14": "recommended-actions schema",
    }

    for sid, (rel, schema_name, fragment) in SCHEMA_TARGETS.items():
        checks.append(
            run_schema_check(sid, schema_names[sid], rel, schema_name, fragment)
        )

    # --- S15 rollup of keyword-level issues already reported ---
    s_results = {c.id: c for c in checks if c.id.startswith("S") and c.id != "S15"}
    if registry is None or schema_load_errors:
        checks.append(
            CheckResult(
                "S15",
                "Enum/required/type/additionalProperties/if-then",
                STATUS_NOT_CHECKED,
                "schema engine unavailable",
            )
        )
    elif any(c.result == STATUS_NOT_CHECKED for c in s_results.values() if c.id.startswith("S") and c.id not in {"S01"}):
        # If some targets not checked due to parse failure, S15 reflects failures among those that ran
        ran = [c for c in s_results.values() if c.id != "S01" and c.result != STATUS_NOT_CHECKED]
        if not ran:
            checks.append(
                CheckResult(
                    "S15",
                    "Enum/required/type/additionalProperties/if-then",
                    STATUS_NOT_CHECKED,
                    "no schema targets runnable after L1 parse failures",
                )
            )
        elif any(c.result == STATUS_FAIL for c in ran):
            checks.append(
                CheckResult(
                    "S15",
                    "Enum/required/type/additionalProperties/if-then",
                    STATUS_FAIL,
                    "schema keyword violations present (see S02–S14)",
                    errors=schema_keyword_failures[:20],
                )
            )
        else:
            checks.append(
                CheckResult(
                    "S15",
                    "Enum/required/type/additionalProperties/if-then",
                    STATUS_PASS,
                    "no keyword violations beyond S02–S14 on runnable targets",
                )
            )
    elif any(c.result == STATUS_FAIL for cid, c in s_results.items() if cid != "S01"):
        checks.append(
            CheckResult(
                "S15",
                "Enum/required/type/additionalProperties/if-then",
                STATUS_FAIL,
                "schema keyword violations present (see S02–S14)",
                errors=schema_keyword_failures[:20],
            )
        )
    else:
        checks.append(
            CheckResult(
                "S15",
                "Enum/required/type/additionalProperties/if-then",
                STATUS_PASS,
                "covered by S02–S14; no additional keyword violations",
            )
        )

    # --- L3-A (Batch A) + deferred L3-B/C stubs ---
    schema_results = {c.id: c.result for c in checks if c.id.startswith("S")}
    for item in run_l3_batch_a(
        package=package,
        parsed_objects=parsed_objects,
        parse_ok=parse_ok,
        schema_results=schema_results,
        manifest_obj=manifest_obj,
    ):
        checks.append(
            CheckResult(
                item.id,
                item.name,
                item.result,
                item.message,
                path=item.path,
                errors=item.errors,
            )
        )

    # --- L4 explicitly NOT_CHECKED ---
    for hid in L4_CHECK_IDS:
        checks.append(
            CheckResult(
                hid,
                f"Semantic boundary {hid}",
                STATUS_NOT_CHECKED,
                "Phase 3B-1: L4 Semantic Review not implemented (never auto semantic PASS)",
            )
        )

    # --- P07 read-only (after all layers; no writes expected) ---
    fingerprint_after = fingerprint_package(package)
    if fingerprint_before != fingerprint_after:
        checks.append(
            CheckResult(
                "P07",
                "Read-only commitment",
                STATUS_FAIL,
                "package file digests changed during validation",
                errors=[
                    {"path": k, "message": "digest changed or file added/removed"}
                    for k in sorted(set(fingerprint_before) | set(fingerprint_after))
                    if fingerprint_before.get(k) != fingerprint_after.get(k)
                ],
            )
        )
    else:
        checks.append(
            CheckResult(
                "P07",
                "Read-only commitment",
                STATUS_PASS,
                "package file digests unchanged after validation",
            )
        )

    cbhf_version = None
    package_id = None
    if isinstance(manifest_obj, dict):
        cbhf_version = manifest_obj.get("cbhf_version")
        package_id = manifest_obj.get("package_id")

    return _finalize_report(
        package=package,
        validated_at=validated_at,
        checks=checks,
        cbhf_version=cbhf_version,
        package_id=package_id,
        limitations=limitations,
        fingerprint_before=fingerprint_before,
        fingerprint_after=fingerprint_after,
    )


def _finalize_report(
    *,
    package: Path,
    validated_at: str,
    checks: list[CheckResult],
    cbhf_version: Any,
    package_id: Any,
    limitations: list[str],
    fingerprint_before: dict[str, str],
    fingerprint_after: dict[str, str],
) -> dict[str, Any]:
    l1 = [c for c in checks if c.id.startswith("P")]
    l2 = [c for c in checks if c.id.startswith("S")]
    l3 = [c for c in checks if c.id.startswith("I")]
    l4 = [c for c in checks if c.id.startswith("H")]

    # Batch A implemented; deferred I* remain NOT_CHECKED → still not_fully_validated.
    final_status = package_final_status(
        checks, l3_implemented=True, l4_reviewed=False
    )

    summary = {
        "pass": sum(1 for c in checks if c.result == STATUS_PASS),
        "fail": sum(1 for c in checks if c.result == STATUS_FAIL),
        "warning": sum(1 for c in checks if c.result == STATUS_WARNING),
        "not_checked": sum(1 for c in checks if c.result == STATUS_NOT_CHECKED),
        "needs_human_review": sum(1 for c in checks if c.result == STATUS_NEEDS_HUMAN),
    }

    return {
        "report_kind": "contextbridge-validation-session",
        "report_version": "0.1.0-validator-draft",
        "cbhf_version": cbhf_version,
        "package_id": package_id,
        "package_label": privacy_label(package),
        "validated_at": validated_at,
        "checker": {
            "name": "context-validator",
            "skill_version": "0.1.0",
            "phase": "3B-B2",
            "scripts_implemented": {
                "L1_package": True,
                "L2_schema": True,
                "L3_integrity": False,
                "L3_A_references": True,
                "L3_B1_path_safety_exists": True,
                "L3_B2_readable_false": True,
                "L3_B_locators": False,
                "L3_C_excerpts": False,
                "L4_semantic": False,
            },
            "wrote_to_package": False,
            "network": False,
        },
        "read_only": fingerprint_before == fingerprint_after,
        "layers": {
            "L1": layer_status(l1),
            "L2": layer_status(l2),
            # Partial L3-A: incompleteness outranks PASS and WARNING at layer level.
            "L3": layer_status(
                l3,
                mixed_pass_not_checked=STATUS_NOT_CHECKED,
                prefer_incomplete_over_warning=True,
            ),
            "L4": STATUS_NOT_CHECKED,
        },
        "checks": [c.to_dict() for c in checks],
        "summary": summary,
        "failures": [c.to_dict() for c in checks if c.result == STATUS_FAIL],
        "warnings": [c.to_dict() for c in checks if c.result == STATUS_WARNING],
        "not_checked": [c.to_dict() for c in checks if c.result == STATUS_NOT_CHECKED],
        "needs_human_review": [
            c.to_dict() for c in checks if c.result == STATUS_NEEDS_HUMAN
        ],
        "final_status": final_status,
        "limitations": limitations,
        "wrote_to_package": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "context-validator Phase 3B-B2 helper: L1 + L2 + L3-A + I11/I10 + I16. "
            "Prints a session JSON report; does not modify the package."
        )
    )
    parser.add_argument(
        "package_root",
        type=Path,
        help="CBHF 0.1.0 package root directory (folder form)",
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=None,
        help="Local schema directory (default: repo spec/cbhf/v0.1.0)",
    )
    args = parser.parse_args(argv)

    report = validate_package(args.package_root, schema_dir=args.schema_dir)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")

    # Exit 1 only on structural FAIL (invalid); warnings / not_fully_validated → 0
    return 1 if report.get("final_status") == "invalid" else 0


if __name__ == "__main__":
    sys.exit(main())
