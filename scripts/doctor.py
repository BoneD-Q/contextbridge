#!/usr/bin/env python3
"""ContextBridge out-of-box doctor checks.

Verifies canonical skills, optional discovery links, schemas, sample package,
and (optionally) runs the Validator helper on the sample package.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_NAMES = (
    "context-exporter",
    "context-validator",
    "context-importer",
)

DISCOVERY_ROOTS = (
    Path(".agents") / "skills",
    Path(".claude") / "skills",
    Path(".cursor") / "skills",
)

REQUIRED_REFS = {
    "context-exporter": (
        "references/cbhf-format.md",
        "references/claim-rules.md",
        "references/evidence-rules.md",
    ),
    "context-validator": (
        "references/validation-rules.md",
        "references/report-format.md",
        "references/semantic-review-boundary.md",
        "scripts/validate_package.py",
    ),
    "context-importer": (
        "references/import-rules.md",
        "references/trust-boundaries.md",
        "references/understanding-report.md",
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class Report:
    def __init__(self) -> None:
        self.ok: list[str] = []
        self.warn: list[str] = []
        self.fail: list[str] = []

    def add_ok(self, msg: str) -> None:
        self.ok.append(msg)

    def add_warn(self, msg: str) -> None:
        self.warn.append(msg)

    def add_fail(self, msg: str) -> None:
        self.fail.append(msg)


def read_frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end]
    for line in block.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def check_canonical(root: Path, r: Report) -> None:
    for name in SKILL_NAMES:
        skill_dir = root / "skills" / name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            r.add_fail(f"missing {skill_md.relative_to(root).as_posix()}")
            continue
        fm_name = read_frontmatter_name(skill_md)
        if fm_name != name:
            r.add_fail(f"frontmatter name {fm_name!r} != folder {name!r}")
        else:
            r.add_ok(f"canonical skill {name}")
        for rel in REQUIRED_REFS[name]:
            path = skill_dir / rel
            if path.is_file():
                r.add_ok(f"  {name}/{rel}")
            else:
                r.add_fail(f"missing {name}/{rel}")


def check_discovery(root: Path, r: Report) -> None:
    any_present = False
    for disc in DISCOVERY_ROOTS:
        base = root / disc
        if not base.is_dir():
            r.add_warn(f"discovery root missing: {disc.as_posix()} (run scripts/install_skills.py)")
            continue
        for name in SKILL_NAMES:
            link = base / name
            canonical = root / "skills" / name
            if not (link.exists() or link.is_symlink()):
                r.add_warn(f"missing link {disc.as_posix()}/{name}")
                continue
            any_present = True
            try:
                if link.resolve() == canonical.resolve():
                    r.add_ok(f"discovery {disc.as_posix()}/{name} -> skills/{name}")
                else:
                    r.add_fail(
                        f"discovery {disc.as_posix()}/{name} resolves to "
                        f"{link.resolve()}, expected {canonical}"
                    )
            except OSError as exc:
                r.add_fail(f"cannot resolve {disc.as_posix()}/{name}: {exc}")
    if any_present:
        r.add_ok("at least one discovery mirror present")


def check_schemas_and_sample(root: Path, r: Report) -> None:
    schema_dir = root / "spec" / "cbhf" / "v0.1.0"
    if schema_dir.is_dir() and any(schema_dir.glob("*.schema.json")):
        r.add_ok(f"schemas present under {schema_dir.relative_to(root).as_posix()}")
    else:
        r.add_fail("missing spec/cbhf/v0.1.0/*.schema.json")

    sample = root / "examples" / "technical-proposal" / "generated-output" / "manifest.yaml"
    if sample.is_file():
        r.add_ok("sample package manifest present")
    else:
        r.add_fail("missing examples/technical-proposal/generated-output/manifest.yaml")

    req = root / "requirements-validator.txt"
    if req.is_file():
        r.add_ok("requirements-validator.txt present")
    else:
        r.add_warn("requirements-validator.txt missing")


def check_python_deps(r: Report) -> None:
    for mod in ("yaml", "jsonschema", "referencing"):
        if importlib.util.find_spec(mod) is None:
            r.add_fail(f"Python package missing: {mod} (pip install -r requirements-validator.txt)")
        else:
            r.add_ok(f"import {mod}")


def run_validator(root: Path, r: Report) -> None:
    script = root / "skills" / "context-validator" / "scripts" / "validate_package.py"
    package = root / "examples" / "technical-proposal" / "generated-output"
    if not script.is_file() or not package.is_dir():
        r.add_fail("cannot run validator smoke: script or sample package missing")
        return
    proc = subprocess.run(
        [sys.executable, str(script), str(package)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode not in (0, 1):
        r.add_fail(f"validate_package crashed (exit {proc.returncode}): {proc.stderr[:500]}")
        return
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        r.add_fail(f"validate_package stdout is not JSON: {exc}")
        return
    final = report.get("final_status")
    wrote = report.get("wrote_to_package")
    if wrote is True:
        r.add_fail("validate_package reported wrote_to_package=true (0.1.0 must be session-only)")
    else:
        r.add_ok("validate_package session-only (wrote_to_package is not true)")
    if final == "invalid" and proc.returncode != 1:
        r.add_fail(f"final_status=invalid but exit code was {proc.returncode}")
    elif final != "invalid" and proc.returncode != 0:
        r.add_fail(f"final_status={final!r} but exit code was {proc.returncode}")
    else:
        r.add_ok(f"validate_package sample final_status={final!r} exit={proc.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-validator",
        action="store_true",
        help="Skip running validate_package on the sample package",
    )
    args = parser.parse_args()
    root = repo_root()
    os.chdir(root)
    r = Report()

    check_canonical(root, r)
    check_discovery(root, r)
    check_schemas_and_sample(root, r)
    check_python_deps(r)
    if not args.skip_validator:
        run_validator(root, r)

    print("ContextBridge doctor")
    print("====================")
    for msg in r.ok:
        print(f"  OK   {msg}")
    for msg in r.warn:
        print(f"  WARN {msg}")
    for msg in r.fail:
        print(f"  FAIL {msg}")
    print(
        f"\nSummary: {len(r.ok)} ok, {len(r.warn)} warn, {len(r.fail)} fail"
    )
    return 1 if r.fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
