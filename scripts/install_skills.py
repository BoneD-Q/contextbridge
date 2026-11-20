#!/usr/bin/env python3
"""Install ContextBridge skills into host discovery directories.

Canonical skill bodies live under repo-root ``skills/``. This script creates
directory links (symlink, or Windows junction) so common Agent Skills hosts
can auto-discover them:

  .agents/skills/<name>   — cross-host convention (Cursor, Codex, OpenCode, …)
  .claude/skills/<name>   — Claude Code
  .cursor/skills/<name>   — Cursor project skills

Idempotent: existing correct links are left alone; wrong targets are replaced.
Does not copy skill files (avoids forking SKILL.md).
"""

from __future__ import annotations

import argparse
import os
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


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def link_exists_to(link: Path, target: Path) -> bool:
    if not link.exists() and not link.is_symlink():
        return False
    try:
        return link.resolve() == target.resolve()
    except OSError:
        return False


def remove_link(link: Path) -> None:
    if link.is_symlink() or link.is_file():
        link.unlink()
        return
    if link.is_dir():
        # Windows junction often reports as directory, not symlink.
        try:
            link.rmdir()
        except OSError:
            # Non-empty real directory — refuse to delete user content.
            raise RuntimeError(
                f"refusing to remove non-empty directory (not a link): {link}"
            ) from None


def create_dir_link(link: Path, target: Path) -> str:
    """Create link at ``link`` pointing to ``target``. Returns method used."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if link_exists_to(link, target):
        return "ok"
    if link.exists() or link.is_symlink():
        remove_link(link)

    # Prefer relative target for portability when using symlink.
    try:
        rel = os.path.relpath(target, start=link.parent)
    except ValueError:
        rel = str(target)

    try:
        os.symlink(rel, link, target_is_directory=True)
        return "symlink"
    except OSError:
        pass

    if os.name == "nt":
        # Directory junction does not require admin / Developer Mode.
        import _winapi  # type: ignore[import-not-found]

        _winapi.CreateJunction(str(target), str(link))
        return "junction"

    # Last resort: absolute symlink retry
    os.symlink(str(target), link, target_is_directory=True)
    return "symlink-abs"


def install(roots: list[Path], *, dry_run: bool) -> int:
    root = repo_root()
    errors = 0
    for name in SKILL_NAMES:
        src = root / "skills" / name
        if not (src / "SKILL.md").is_file():
            print(f"ERROR missing canonical skill: {src / 'SKILL.md'}", file=sys.stderr)
            errors += 1
            continue
        for disc in roots:
            link = root / disc / name
            if dry_run:
                print(f"DRY-RUN would link {link} -> {src}")
                continue
            try:
                method = create_dir_link(link, src)
                print(f"{method:10} {disc.as_posix()}/{name} -> skills/{name}")
            except OSError as exc:
                print(f"ERROR {link}: {exc}", file=sys.stderr)
                errors += 1
            except RuntimeError as exc:
                print(f"ERROR {exc}", file=sys.stderr)
                errors += 1
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned links without creating them",
    )
    parser.add_argument(
        "--agents-only",
        action="store_true",
        help="Only install under .agents/skills",
    )
    args = parser.parse_args()
    roots = [Path(".agents") / "skills"] if args.agents_only else list(DISCOVERY_ROOTS)
    errors = install(roots, dry_run=args.dry_run)
    if errors:
        print(f"Finished with {errors} error(s).", file=sys.stderr)
        return 1
    print("Install complete. Canonical skills remain under skills/; discovery dirs are mirrors only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
