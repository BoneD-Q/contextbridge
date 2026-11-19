#!/usr/bin/env python3
"""Deterministic CBHF package smoke test (NOT context-validator).

Checks required paths, YAML/JSON parse, Draft 2020-12 schemas, and basic
id-link presence. Does not judge evidence adequacy or conflict policy quality.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "spec" / "cbhf" / "v0.1.0"
DEFAULT_PACKAGE = ROOT / "examples/technical-proposal/generated-output"

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

JSON_SCHEMA_MAP = {
    "source/source-index.json": "source.schema.json",
    "knowledge/facts.json": "fact.schema.json",
    "knowledge/claims.json": "claim.schema.json",
    "knowledge/decisions.json": "decision.schema.json",
    "knowledge/constraints.json": "constraint.schema.json",
    "knowledge/glossary.json": "glossary.schema.json",
    "evidence/evidence.json": "evidence.schema.json",
    "uncertainty/unknowns.json": "unknown.schema.json",
    "uncertainty/conflicts.json": "conflict.schema.json",
    "handoff/questions.json": "questions.schema.json",
    "handoff/recommended-actions.json": "recommended-actions.schema.json",
}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


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


def build_registry() -> Registry:
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.schema.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(data, default_specification=DRAFT202012)
        registry = registry.with_resource(data["$id"], resource)
        registry = registry.with_resource(path.name, resource)
    return registry


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    package = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PACKAGE
    failures: list[str] = []
    passes = 0

    print(f"Package smoke test (NOT Validator): {package}")

    # required paths
    for rel in REQUIRED_PATHS:
        p = package / rel
        if not p.exists():
            failures.append(f"missing required path: {rel}")
        else:
            print(f"PASS exists {rel}")
            passes += 1

    # must not invent validation report
    if (package / "validation").exists() or (
        package / "validation/validation-report.json"
    ).exists():
        failures.append("validation/ must not be created by exporter")
    else:
        print("PASS no validation/ directory")
        passes += 1

    registry = build_registry()

    # manifest YAML
    try:
        manifest = yaml.load(
            (package / "manifest.yaml").read_text(encoding="utf-8"),
            Loader=UniqueKeyLoader,
        )
        schema = load_json(SCHEMA_DIR / "manifest.schema.json")
        Draft202012Validator.check_schema(schema)
        errors = list(
            Draft202012Validator(schema, registry=registry).iter_errors(manifest)
        )
        if errors:
            failures.append(f"manifest schema: {errors[0].message}")
        else:
            print("PASS manifest.yaml schema")
            passes += 1
        if manifest.get("validation", {}).get("present") is not False:
            failures.append("manifest.validation.present must be false for exporter")
        else:
            print("PASS validation.present is false")
            passes += 1
    except Exception as exc:
        failures.append(f"manifest parse/validate: {exc}")

    # references via fragment
    try:
        refs = load_json(package / "evidence/references.json")
        wrapped = {
            "$ref": (
                "https://contextbridge.dev/spec/cbhf/v0.1.0/evidence.schema.json"
                "#/$defs/ReferencesDocument"
            )
        }
        errors = list(
            Draft202012Validator(wrapped, registry=registry).iter_errors(refs)
        )
        if errors:
            failures.append(f"references schema: {errors[0].message}")
        else:
            print("PASS evidence/references.json schema")
            passes += 1
    except Exception as exc:
        failures.append(f"references: {exc}")

    # JSON files + schemas
    loaded = {}
    for rel, schema_name in JSON_SCHEMA_MAP.items():
        try:
            data = load_json(package / rel)
            loaded[rel] = data
            schema = load_json(SCHEMA_DIR / schema_name)
            Draft202012Validator.check_schema(schema)
            errors = list(
                Draft202012Validator(schema, registry=registry).iter_errors(data)
            )
            if errors:
                failures.append(f"{rel}: {errors[0].message}")
            else:
                print(f"PASS schema {rel}")
                passes += 1
        except Exception as exc:
            failures.append(f"{rel}: {exc}")

    # empty-collection shape
    for rel, key in [
        ("evidence/references.json", "references"),
    ]:
        data = loaded.get(rel) or load_json(package / rel)
        if key not in data or not isinstance(data[key], list):
            failures.append(f"{rel} missing array key {key}")
        else:
            print(f"PASS empty-collection shape {rel}")
            passes += 1

    # basic link integrity
    try:
        sources = {
            s["source_id"] for s in loaded["source/source-index.json"]["sources"]
        }
        evidence = {e["evidence_id"]: e for e in loaded["evidence/evidence.json"]["evidence"]}
        facts = {f["fact_id"]: f for f in loaded["knowledge/facts.json"]["facts"]}
        claims = {c["claim_id"]: c for c in loaded["knowledge/claims.json"]["claims"]}
        decisions = {
            d["decision_id"]: d for d in loaded["knowledge/decisions.json"]["decisions"]
        }
        constraints = {
            c["constraint_id"]: c
            for c in loaded["knowledge/constraints.json"]["constraints"]
        }
        terms = {t["term_id"]: t for t in loaded["knowledge/glossary.json"]["terms"]}
        knowledge = {
            "fact": facts,
            "claim": claims,
            "decision": decisions,
            "constraint": constraints,
            "term": terms,
        }

        # evidence locators source_id + path exist
        for eid, ev in evidence.items():
            loc = ev["locator"]
            if loc["source_id"] not in sources:
                failures.append(f"{eid} unknown source_id {loc['source_id']}")
            path = package / loc["path"]
            if not path.exists():
                failures.append(f"{eid} missing path {loc['path']}")
            # line_range excerpt presence (deterministic check)
            if loc["locator_type"] == "line_range" and loc["start"] is not None:
                lines = path.read_text(encoding="utf-8").splitlines()
                start = int(loc["start"])
                end = int(loc["end"] if loc["end"] is not None else loc["start"])
                if start < 1 or end > len(lines):
                    failures.append(f"{eid} line_range out of bounds")
                else:
                    span = "\n".join(lines[start - 1 : end])
                    # first line of excerpt should appear in span
                    first = loc["excerpt"].splitlines()[0]
                    if first not in span:
                        failures.append(
                            f"{eid} excerpt first line not found at locator"
                        )

        # bidirectional evidence_ids <-> supports
        for eid, ev in evidence.items():
            for sup in ev.get("supports", []):
                bucket = knowledge.get(sup["type"], {})
                obj = bucket.get(sup["id"])
                if obj is None:
                    failures.append(f"{eid} supports missing {sup['type']}:{sup['id']}")
                elif eid not in obj.get("evidence_ids", []):
                    failures.append(
                        f"{eid} not listed in {sup['id']}.evidence_ids"
                    )

        for kind, bucket in knowledge.items():
            for kid, obj in bucket.items():
                for eid in obj.get("evidence_ids", []):
                    if eid not in evidence:
                        failures.append(f"{kid} evidence_ids unknown {eid}")
                    else:
                        ok = any(
                            s.get("id") == kid and s.get("type") == kind
                            for s in evidence[eid].get("supports", [])
                        )
                        if not ok:
                            failures.append(
                                f"{kid} missing reverse supports in {eid}"
                            )
                if obj.get("status") == "verified" and not obj.get("evidence_ids"):
                    failures.append(f"{kid} verified without evidence_ids")
                if obj.get("status") == "user_confirmed":
                    conf = obj.get("confirmation")
                    if not isinstance(conf, dict):
                        failures.append(f"{kid} user_confirmed without confirmation")

        # conflict party ids
        for cfl in loaded["uncertainty/conflicts.json"]["conflicts"]:
            for party in cfl.get("parties", []):
                bucket = knowledge.get(party["type"], {})
                if party["id"] not in bucket:
                    failures.append(
                        f"{cfl['conflict_id']} party missing {party['type']}:{party['id']}"
                    )

        if not any(f.startswith("ev_") or "supports" in f or "evidence" in f for f in failures):
            # only print pass if no link failures accumulated in this section
            link_fails = [
                f
                for f in failures
                if any(
                    k in f
                    for k in (
                        "supports",
                        "evidence_ids",
                        "source_id",
                        "missing path",
                        "line_range",
                        "excerpt",
                        "verified without",
                        "user_confirmed",
                        "party missing",
                    )
                )
            ]
            if not link_fails:
                print("PASS basic id/link integrity")
                passes += 1
    except Exception as exc:
        failures.append(f"link integrity: {exc}")

    # secrets must not appear in package text (best-effort smoke)
    banned = [
        "nw_stg_example_token_DO_NOT_SHIP_9f3a",
        "SuperSecret!StagingOnly",
        "ReplaceMeToken",
    ]
    for path in package.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".json", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in banned:
                if token in text:
                    failures.append(f"secret leak in {path.relative_to(package)}: {token}")
    if not any("secret leak" in f for f in failures):
        print("PASS no known plaintext secrets in package")
        passes += 1

    print(f"\nSmoke summary: {passes} checks passed, {len(failures)} failed")
    print(
        "NOTE: This is structural smoke only — not context-validator, "
        "not semantic adequacy certification."
    )
    for f in failures:
        print(f"FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
