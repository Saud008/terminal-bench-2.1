#!/usr/bin/env python3
"""Move .cursor/rules/*.mdc to archive/ — leave only terminus.mdc in .cursor/rules/."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / ".cursor" / "rules"
ARCHIVE = REPO / "archive" / "terminus-rules-mdc"
KEEP = {"terminus.mdc"}


def main() -> int:
    if not RULES.is_dir():
        print("No .cursor/rules/")
        return 1

    moved = 0
    for path in sorted(RULES.rglob("*.mdc")):
        rel = path.relative_to(RULES)
        if rel.as_posix() in KEEP or rel.name in KEEP:
            continue
        dest = ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        shutil.move(str(path), str(dest))
        print(f"archive  {rel}")
        moved += 1

    # Remove empty dirs under rules/
    for d in sorted(RULES.rglob("*"), reverse=True):
        if d.is_dir() and d != RULES:
            try:
                d.rmdir()
            except OSError:
                pass

    print(f"\nMoved {moved} .mdc → archive/terminus-rules-mdc/")
    print("Kept: .cursor/rules/terminus.mdc only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
