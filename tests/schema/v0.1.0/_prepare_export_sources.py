"""Deterministic helper: copy+redact technical-proposal inputs into generated-output."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INP = ROOT / "examples/technical-proposal/input"
OUT = ROOT / "examples/technical-proposal/generated-output"

PATTERNS = [
    (re.compile(r"(EDGE_BOOTSTRAP_TOKEN=)\S+"), r"\1[REDACTED:token]"),
    (re.compile(r"(DB_PASSWORD=)\S+"), r"\1[REDACTED:password]"),
    (re.compile(r"(PAGER_WEBHOOK_URL=)https://\S+"), r"\1[REDACTED:token]"),
]

FILES = [
    "architecture-overview.md",
    "ops-runbook-excerpt.md",
    "decision-record.md",
    "open-questions.md",
]


def main() -> None:
    if OUT.exists():
        # keep regenerating source/original only; caller may overwrite other files
        src_dir = OUT / "source/original"
        if src_dir.exists():
            shutil.rmtree(src_dir)
    for sub in [
        "source/original",
        "knowledge",
        "evidence",
        "uncertainty",
        "handoff",
    ]:
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    index = []
    for i, name in enumerate(FILES, 1):
        src = INP / name
        raw = src.read_text(encoding="utf-8")
        text = raw
        for pat, repl in PATTERNS:
            text = pat.sub(repl, text)
        transformed = text != raw
        # normalize newlines to \n for stable locators
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.endswith("\n"):
            text += "\n"
        dest = OUT / "source/original" / name
        dest.write_text(text, encoding="utf-8", newline="\n")
        lines = text.splitlines()
        sid = f"src_{i:03d}"
        lang = "mixed" if name == "decision-record.md" else "en"
        index.append(
            {
                "source_id": sid,
                "original_name": name,
                "user_path": f"examples/technical-proposal/input/{name}",
                "package_path": f"source/original/{name}",
                "media_type": "text/markdown",
                "language": lang,
                "role": "primary" if i == 1 else "supporting",
                "received_from": "workspace",
                "content_transformed": transformed,
                "transform_reason": "redaction" if transformed else "none",
                "readable": True,
                "notes": (
                    "Package copy; user original left untouched."
                    + (" Secrets masked." if transformed else "")
                ),
                "checksum": {
                    "alg": "sha256",
                    "value": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "of": "package_copy",
                },
            }
        )
        print(f"=== {sid} {name} transformed={transformed} lines={len(lines)}")
        for n, line in enumerate(lines, 1):
            print(f"{n:3d}|{line}")
        print()

    (OUT / "source/source-index.json").write_text(
        json.dumps({"sources": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Wrote source-index.json")


if __name__ == "__main__":
    main()
