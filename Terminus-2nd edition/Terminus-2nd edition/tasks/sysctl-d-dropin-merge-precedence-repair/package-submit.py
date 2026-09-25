#!/usr/bin/env python3
"""Build flat-root submission zip."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / "tasksubmit" / "sysctl-d-dropin-merge-precedence-repair.zip"
SKIP = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "package-submit.py",
    "rubric.md",
    "collapse_check.py",
    "verify-local.sh",
    "output",
    "jobs",
}


def should_skip(rel: Path) -> bool:
    return bool(set(rel.parts) & SKIP) or rel.suffix == ".pyc"


def unix_external_attr(path: Path) -> int:
    mode = 0o755 if path.suffix == ".sh" else 0o644
    return (stat.S_IFREG | mode) << 16


def add_path(zf: zipfile.ZipFile, src: Path, arc: str) -> None:
    info = zipfile.ZipInfo(arc)
    info.external_attr = unix_external_attr(src)
    data = src.read_bytes()
    if src.suffix == ".sh":
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    zf.writestr(info, data)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(ROOT)
            if should_skip(rel):
                continue
            add_path(zf, path, rel.as_posix())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
