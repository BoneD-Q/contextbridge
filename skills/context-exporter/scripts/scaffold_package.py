#!/usr/bin/env python3
"""Scaffold an empty CBHF 0.1.0 folder package for context-exporter.

Creates the Exporter-required tree with schema-shaped empty collections and
stub narratives so an Agent can fill content without inventing layout.

Does NOT copy sources, extract knowledge, or run Validator.
Does NOT create validation/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_VERSION = "0.1.1"

EMPTY_JSON: dict[str, object] = {
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

DIRS = (
    "source/original",
    "knowledge",
    "evidence",
    "uncertainty",
    "handoff",
)

OVERVIEW_STUB = """# 概览 / Overview

## zh
（脚手架占位 — 请用源文档改写。说明范围与非目标。）

## en
(Scaffold stub — replace from sources. State scope and non-goals.)
"""

RECEIVER_STUB = """# Receiver guide / 接收方指南

## zh
- **目的**：（脚手架占位）说明本包交接目标。
- **信任边界**：按条目 KnowledgeStatus；Unknown 保持 OPEN；勿自动裁决冲突。
- **包内副本**：见 `source/original/` 与 `source/source-index.json`。
- **限制**：脚手架未摄入来源；导出完成后更新本段与 `manifest.limitations`。

## en
- **Purpose**: (scaffold stub) state handoff goal.
- **Trust boundary**: honor KnowledgeStatus; keep Unknowns OPEN; do not auto-resolve conflicts.
- **Packaged copies**: see `source/original/` and `source/source-index.json`.
- **Limitations**: scaffold ingested no sources; update this section and `manifest.limitations` after export.
"""


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(
    pkg: Path,
    *,
    package_id: str,
    title_zh: str,
    title_en: str,
    primary_lang: str,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    files = [
        "manifest.yaml",
        *EMPTY_JSON.keys(),
        "knowledge/overview.md",
        "handoff/receiver-guide.md",
    ]
    touched = "\n".join(f"    - {f}" for f in files)
    text = f"""cbhf_version: "0.1.0"
protocol: CBHF
package_id: {json.dumps(package_id, ensure_ascii=False)}
title:
  zh: {json.dumps(title_zh, ensure_ascii=False)}
  en: {json.dumps(title_en, ensure_ascii=False)}
scenario: docs
package_form: folder
generated_at: "{now}"
generator:
  skill: context-exporter
  skill_version: "{SKILL_VERSION}"
locale:
  narratives:
    - zh
    - en
  primary_source_lang: {primary_lang}
sources_summary:
  count: 0
  source_ids: []
integrity:
  files_touched:
{touched}
limitations:
  - "Scaffold only: no sources ingested yet; Agent must copy sources and fill knowledge."
  - "Redaction is best-effort; not applied at scaffold time."
  - "Absence of validation/ means not validated yet."
  - "integrity.files_touched is a write inventory only and does not mean integrity verification passed."
redaction:
  applied: false
  policy: default_secrets_and_pii
  completeness: best_effort
  notes: "Scaffold created empty tree; no redaction performed."
validation:
  present: false
  report_path: null
notes: "Created by skills/context-exporter/scripts/scaffold_package.py — fill before Validator."
"""
    (pkg / "manifest.yaml").write_text(text, encoding="utf-8")


def scaffold(
    package_root: Path,
    *,
    package_id: str,
    title_zh: str,
    title_en: str,
    primary_lang: str,
    force: bool,
) -> None:
    package_root = package_root.resolve()
    if package_root.exists():
        if any(package_root.iterdir()) and not force:
            raise SystemExit(
                f"refusing non-empty directory (pass --force to allow): {package_root}"
            )
        if (package_root / "manifest.yaml").is_file() and not force:
            raise SystemExit(
                f"refusing existing package root (pass --force): {package_root}"
            )
    package_root.mkdir(parents=True, exist_ok=True)

    for d in DIRS:
        (package_root / d).mkdir(parents=True, exist_ok=True)

    for rel, obj in EMPTY_JSON.items():
        write_json(package_root / rel, obj)

    (package_root / "knowledge" / "overview.md").write_text(OVERVIEW_STUB, encoding="utf-8")
    (package_root / "handoff" / "receiver-guide.md").write_text(RECEIVER_STUB, encoding="utf-8")
    # Keep original/ present but empty (no .gitkeep required by protocol).
    write_manifest(
        package_root,
        package_id=package_id,
        title_zh=title_zh,
        title_en=title_en,
        primary_lang=primary_lang,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package_root",
        type=Path,
        help="Path that will become the CBHF package root (must be empty unless --force)",
    )
    parser.add_argument("--package-id", required=True, help="Stable package_id")
    parser.add_argument("--title-zh", default="", help="Chinese title (default from id)")
    parser.add_argument("--title-en", default="", help="English title (default from id)")
    parser.add_argument(
        "--primary-lang",
        default="zh",
        choices=("zh", "en", "mixed"),
        help="manifest.locale.primary_source_lang",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow writing into an existing/non-empty directory (overwrites scaffold files)",
    )
    args = parser.parse_args()
    title_zh = args.title_zh or args.package_id
    title_en = args.title_en or args.package_id
    try:
        scaffold(
            args.package_root,
            package_id=args.package_id,
            title_zh=title_zh,
            title_en=title_en,
            primary_lang=args.primary_lang,
            force=args.force,
        )
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"scaffolded {args.package_root.resolve()}")
    print("next: copy sources into source/original/, fill knowledge/evidence, update manifest")
    print("then: python skills/context-validator/scripts/validate_package.py <package-root>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
