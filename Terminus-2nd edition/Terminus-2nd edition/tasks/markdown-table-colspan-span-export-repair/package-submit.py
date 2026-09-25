#!/usr/bin/env python3
"""Build flat-root submission zip."""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent / "tasksubmit" / "markdown-table-colspan-span-export-repair.zip"
SKIP = {"__pycache__", ".pytest_cache", "jobs", "target", ".gitattributes", "rubric.md"}

TEXT_LF_SUFFIXES = {".sh", ".json", ".md", ".rs", ".toml", ".lock", ".py"}


def should_skip(path: Path) -> bool:
    if path.suffix == ".pyc":
        return True
    return bool(set(path.parts) & SKIP)


def unix_external_attr(path: Path) -> int:
    mode = 0o755 if path.suffix == ".sh" else 0o644
    return (stat.S_IFREG | mode) << 16


def normalize_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def add_path(zf: zipfile.ZipFile, src: Path, arc: str) -> None:
    info = zipfile.ZipInfo(arc)
    info.external_attr = unix_external_attr(src)
    data = src.read_bytes()
    if src.suffix in TEXT_LF_SUFFIXES or src.name in {"Dockerfile", ".dockerignore"}:
        data = normalize_lf(data)
    zf.writestr(info, data)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and not should_skip(path.relative_to(ROOT)):
                rel = path.relative_to(ROOT).as_posix()
                if rel in {"package-submit.py", "verify-local.sh"}:
                    continue
                add_path(zf, path, rel)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
