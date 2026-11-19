#!/usr/bin/env python3
"""Run CBHF 0.1.0 JSON Schema fixtures and YAML→manifest pipeline tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "spec" / "cbhf" / "v0.1.0"
FIXTURE_DIR = Path(__file__).resolve().parent

# --- Original baseline (must remain 11 loads + 16 fixtures = 27) ---
BASELINE_SCHEMA_FILES = [
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
]

BASELINE_CASES = [
    ("valid/minimal_manifest.json", "manifest.schema.json", None, True),
    ("valid/minimal_source.json", "source.schema.json", None, True),
    ("valid/minimal_claims.json", "claim.schema.json", None, True),
    ("valid/minimal_facts.json", "fact.schema.json", None, True),
    ("valid/minimal_decisions.json", "decision.schema.json", None, True),
    ("valid/minimal_constraints.json", "constraint.schema.json", None, True),
    ("valid/minimal_glossary.json", "glossary.schema.json", None, True),
    ("valid/minimal_evidence.json", "evidence.schema.json", None, True),
    (
        "valid/minimal_references.json",
        "evidence.schema.json",
        "#/$defs/ReferencesDocument",
        True,
    ),
    ("valid/minimal_unknowns.json", "unknown.schema.json", None, True),
    ("valid/minimal_conflicts.json", "conflict.schema.json", None, True),
    ("invalid/missing_required_manifest.json", "manifest.schema.json", None, False),
    (
        "invalid/illegal_status_reference.json",
        "evidence.schema.json",
        "#/$defs/ReferencesDocument",
        False,
    ),
    (
        "invalid/wrong_type_content_transformed.json",
        "source.schema.json",
        None,
        False,
    ),
    ("invalid/verified_without_evidence.json", "fact.schema.json", None, False),
    (
        "invalid/section_locator_number_start.json",
        "evidence.schema.json",
        None,
        False,
    ),
]

# --- Additive schemas / fixtures (do not replace baseline) ---
NEW_SCHEMA_FILES = [
    "questions.schema.json",
    "recommended-actions.schema.json",
]

NEW_CASES = [
    ("valid/minimal_questions.json", "questions.schema.json", None, True),
    (
        "valid/minimal_recommended_actions.json",
        "recommended-actions.schema.json",
        None,
        True,
    ),
    (
        "invalid/action_status_completed.json",
        "recommended-actions.schema.json",
        None,
        False,
    ),
]

SCHEMA_FILES = BASELINE_SCHEMA_FILES + NEW_SCHEMA_FILES


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
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


def load_yaml_unique(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


def build_registry() -> Registry:
    registry = Registry()
    for name in SCHEMA_FILES:
        path = SCHEMA_DIR / name
        data = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(data, default_specification=DRAFT202012)
        registry = registry.with_resource(data["$id"], resource)
        registry = registry.with_resource(name, resource)
    return registry


def load_schema(registry: Registry, schema_name: str, fragment: str | None):
    schema_path = SCHEMA_DIR / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    if fragment:
        wrapped = {"$ref": f"{schema['$id']}{fragment}"}
        return wrapped, registry
    return schema, registry


def run_schema_loads(names: list[str], label: str) -> tuple[int, list[str]]:
    passes = 0
    failures: list[str] = []
    print(f"== Schema load ({label}) ==")
    for name in names:
        path = SCHEMA_DIR / name
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            print(f"PASS load {name}")
            passes += 1
        except (json.JSONDecodeError, SchemaError) as exc:
            msg = f"FAIL load {name}: {exc}"
            print(msg)
            failures.append(msg)
    return passes, failures


def run_fixture_cases(
    cases: list[tuple],
    registry: Registry,
    label: str,
) -> tuple[int, list[str]]:
    passes = 0
    failures: list[str] = []
    print(f"\n== Fixture validation ({label}) ==")
    for rel, schema_name, fragment, expect_valid in cases:
        fixture_path = FIXTURE_DIR / rel
        instance = json.loads(fixture_path.read_text(encoding="utf-8"))
        schema, reg = load_schema(registry, schema_name, fragment)
        validator = Draft202012Validator(schema, registry=reg)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        is_valid = len(errors) == 0
        ok = is_valid == expect_valid
        expect_label = "valid" if expect_valid else "invalid"
        if ok:
            print(f"PASS expect={expect_label} {rel}")
            passes += 1
        else:
            detail = "; ".join(
                f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                for e in errors[:3]
            ) or "expected errors but instance validated"
            msg = f"FAIL expect={expect_label} {rel} :: {detail}"
            print(msg)
            failures.append(msg)
    return passes, failures


def run_yaml_pipeline(registry: Registry) -> tuple[int, list[str]]:
    passes = 0
    failures: list[str] = []
    print("\n== YAML → Schema pipeline ==")

    manifest_schema, reg = load_schema(registry, "manifest.schema.json", None)
    source_schema, reg2 = load_schema(registry, "source.schema.json", None)

    # 1) valid manifest.yaml
    path = FIXTURE_DIR / "yaml/valid/manifest_minimal.yaml"
    try:
        obj = load_yaml_unique(path)
        errors = list(Draft202012Validator(manifest_schema, registry=reg).iter_errors(obj))
        if errors:
            raise AssertionError(errors[0].message)
        print(f"PASS yaml valid manifest {path.name}")
        passes += 1
    except Exception as exc:
        msg = f"FAIL yaml valid manifest: {exc}"
        print(msg)
        failures.append(msg)

    # 2) missing required field
    path = FIXTURE_DIR / "yaml/invalid/manifest_missing_limitations.yaml"
    try:
        obj = load_yaml_unique(path)
        errors = list(
            Draft202012Validator(manifest_schema, registry=reg).iter_errors(obj)
        )
        if not errors:
            raise AssertionError("expected schema errors for missing limitations")
        print(f"PASS yaml invalid missing-required {path.name}")
        passes += 1
    except Exception as exc:
        msg = f"FAIL yaml missing-required: {exc}"
        print(msg)
        failures.append(msg)

    # 3) illegal enum
    path = FIXTURE_DIR / "yaml/invalid/manifest_illegal_scenario.yaml"
    try:
        obj = load_yaml_unique(path)
        errors = list(
            Draft202012Validator(manifest_schema, registry=reg).iter_errors(obj)
        )
        if not errors:
            raise AssertionError("expected schema errors for illegal scenario")
        print(f"PASS yaml invalid illegal-enum {path.name}")
        passes += 1
    except Exception as exc:
        msg = f"FAIL yaml illegal-enum: {exc}"
        print(msg)
        failures.append(msg)

    # 4) content_transformed true/false/null via YAML source-index
    path = FIXTURE_DIR / "yaml/valid/source_content_transformed_values.yaml"
    try:
        obj = load_yaml_unique(path)
        values = [s.get("content_transformed") for s in obj["sources"]]
        if values != [True, False, None]:
            raise AssertionError(f"unexpected content_transformed values: {values}")
        errors = list(
            Draft202012Validator(source_schema, registry=reg2).iter_errors(obj)
        )
        if errors:
            raise AssertionError(errors[0].message)
        print(f"PASS yaml content_transformed tri-state {path.name}")
        passes += 1
    except Exception as exc:
        msg = f"FAIL yaml content_transformed: {exc}"
        print(msg)
        failures.append(msg)

    # 5) bad YAML syntax
    path = FIXTURE_DIR / "yaml/invalid/manifest_bad_syntax.yaml"
    try:
        try:
            load_yaml_unique(path)
            raise AssertionError("expected YAML parse error")
        except yaml.YAMLError:
            print(f"PASS yaml bad-syntax rejected {path.name}")
            passes += 1
    except Exception as exc:
        msg = f"FAIL yaml bad-syntax: {exc}"
        print(msg)
        failures.append(msg)

    # 6) duplicate keys must not silently overwrite
    path = FIXTURE_DIR / "yaml/invalid/manifest_duplicate_keys.yaml"
    try:
        try:
            load_yaml_unique(path)
            raise AssertionError("expected duplicate-key error")
        except yaml.constructor.ConstructorError as exc:
            if "duplicate key" not in str(exc):
                raise
            print(f"PASS yaml duplicate-keys rejected {path.name}")
            passes += 1
    except Exception as exc:
        msg = f"FAIL yaml duplicate-keys: {exc}"
        print(msg)
        failures.append(msg)

    return passes, failures


def main() -> int:
    registry = build_registry()
    failures: list[str] = []
    passes = 0

    p, f = run_schema_loads(BASELINE_SCHEMA_FILES, "baseline Draft 2020-12")
    passes += p
    failures.extend(f)

    p, f = run_fixture_cases(BASELINE_CASES, registry, "baseline")
    passes += p
    failures.extend(f)

    baseline_total = len(BASELINE_SCHEMA_FILES) + len(BASELINE_CASES)
    print(f"\nBaseline subtotal: {passes}/{baseline_total} (expected {baseline_total})")
    if passes < baseline_total or any("baseline" in x or x.startswith("FAIL load") for x in failures):
        # Still continue additive tests, but baseline regression is fatal at end.
        pass
    if baseline_total != 27:
        failures.append(
            f"FAIL baseline count drift: expected 27 slots, found {baseline_total}"
        )

    p, f = run_schema_loads(NEW_SCHEMA_FILES, "new handoff schemas")
    passes += p
    failures.extend(f)

    p, f = run_fixture_cases(NEW_CASES, registry, "new handoff fixtures")
    passes += p
    failures.extend(f)

    p, f = run_yaml_pipeline(registry)
    passes += p
    failures.extend(f)

    print(f"\nSummary: {passes} passed, {len(failures)} failed")
    if baseline_total == 27:
        print("Baseline retention: 27 original test slots preserved.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
