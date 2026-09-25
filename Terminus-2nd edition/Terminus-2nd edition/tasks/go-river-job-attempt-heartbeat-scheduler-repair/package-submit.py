#!/usr/bin/env python3
"""Build flat-root submission zip."""

from __future__ import annotations

import zipfile
from pathlib import Path

TASK = Path(__file__).resolve().parent
OUT = TASK.parents[1] / "tasksubmit" / f"{TASK.name}.zip"
SKIP = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "package-submit.py",
    "logs-nop",
    "logs-oracle",
    "rubric.md",
}


def skip(path: Path) -> bool:
    return any(part in SKIP for part in path.parts) or path.suffix == ".pyc"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(TASK.rglob("*")):
            if path.is_dir() or skip(path):
                continue
            zf.write(path, path.relative_to(TASK).as_posix())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
