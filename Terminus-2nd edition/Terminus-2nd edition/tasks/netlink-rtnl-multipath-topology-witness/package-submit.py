#!/usr/bin/env python3
"""Build flat-root submission zip."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / "tasksubmit" / "netlink-route-nexthop-multipath-bind-repair.zip"
SKIP = {
    "__pycache__",
    ".pytest_cache",
    "package-submit.py",
    "_generate_fixtures.py",
    "rubric.md",
    "target",
}


def should_skip(path: Path) -> bool:
    return bool(set(path.parts) & SKIP) or path.suffix == ".pyc"


def unix_external_attr(path: Path) -> int:
    mode = 0o755 if path.suffix == ".sh" else 0o644
    return (stat.S_IFREG | mode) << 16


def add_path(zf: zipfile.ZipFile, src: Path, arc: str) -> None:
    info = zipfile.ZipInfo(arc)
    info.external_attr = unix_external_attr(src)
    data = src.read_bytes()
    if src.suffix in {".sh", ".py"}:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    zf.writestr(info, data)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and not should_skip(path.relative_to(ROOT)):
                arc = path.relative_to(ROOT).as_posix()
                add_path(zf, path, arc)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
