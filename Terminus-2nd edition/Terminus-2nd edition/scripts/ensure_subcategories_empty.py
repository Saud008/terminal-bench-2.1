#!/usr/bin/env python3
"""Ensure task.toml uses subcategories = [] (repo policy)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EMPTY_LINE = "subcategories = []"
HAS_EMPTY = re.compile(r"^subcategories\s*=\s*\[\]\s*$", re.MULTILINE)
HAS_ANY = re.compile(r"^subcategories\s*=.*$", re.MULTILINE)
METADATA = re.compile(r"^\[metadata\]\s*$", re.MULTILINE)


def resolve_task_dir(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def ensure_task_toml(path: Path, *, write: bool) -> tuple[bool, bool]:
    """Return (ok, changed)."""
    if not path.is_file():
        print(f"ERROR: missing {path}", file=sys.stderr)
        return False, False

    text = path.read_text(encoding="utf-8")
    if HAS_EMPTY.search(text):
        return True, False

    if HAS_ANY.search(text):
        new_text = HAS_ANY.sub(EMPTY_LINE, text, count=1)
    else:
        m = METADATA.search(text)
        if not m:
            print(f"ERROR: no [metadata] in {path}", file=sys.stderr)
            return False, False
        insert_at = m.end()
        if insert_at < len(text) and text[insert_at] != "\n":
            insert_at += 1
        new_text = text[:insert_at] + f"\n{EMPTY_LINE}" + text[insert_at:]

    if write and new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True, True

    if new_text != text:
        return False, True  # would change but not writing

    return True, False


def iter_task_tomls(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        out.extend(sorted(root.glob("**/task.toml")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=str, help="Single task folder (tasks/<name> or tasksss/<name>)")
    parser.add_argument("--check", action="store_true", help="Verify only; exit 1 if not empty")
    parser.add_argument("--ensure", action="store_true", help="Auto-fix then verify (for pack_zip)")
    parser.add_argument("--quiet", action="store_true", help="No output on success")
    args = parser.parse_args()

    write = not args.check
    if args.ensure:
        write = True

    if args.task_dir:
        task_dir = resolve_task_dir(args.task_dir)
        paths = [task_dir / "task.toml"]
    else:
        paths = iter_task_tomls(
            [REPO_ROOT / "tasks", REPO_ROOT / "pending", REPO_ROOT / "tasksss", REPO_ROOT / "dusre-wale"]
        )

    bad: list[Path] = []
    changed: list[Path] = []

    for path in paths:
        if not path.is_file():
            continue
        ok, did_change = ensure_task_toml(path, write=write)
        if did_change:
            changed.append(path)
        if not ok:
            bad.append(path)

    if changed and not args.quiet:
        for p in changed:
            print(f"FIX  {p.relative_to(REPO_ROOT)}")

    if bad:
        for p in bad:
            print(f"FAIL {p.relative_to(REPO_ROOT)}", file=sys.stderr)
        print("ERROR: subcategories must be [] — see .cursor/rules/shared/task-toml-subcategories-gate.mdc", file=sys.stderr)
        return 1

    if not args.quiet and not args.task_dir:
        print(f"OK: {len(paths)} task.toml — subcategories = []")
    elif not args.quiet and args.task_dir:
        print("OK: subcategories = []")

    return 0


if __name__ == "__main__":
    sys.exit(main())
