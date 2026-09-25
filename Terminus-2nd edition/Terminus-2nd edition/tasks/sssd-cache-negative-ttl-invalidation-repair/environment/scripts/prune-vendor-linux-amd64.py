#!/usr/bin/env python3
"""Drop non-linux/amd64 modernc.org platform blobs from vendored deps."""

from __future__ import annotations

import re
from pathlib import Path

KEEP_SQLITE = {"sqlite_linux_amd64.go", "mutex.go", "hooks.go", "defs.go"}

NON_LINUX_AMD64 = re.compile(
    r"_(windows|darwin|freebsd|openbsd|netbsd|illumos|aix|solaris)(_|\.|$)"
    r"|_linux_(386|arm|arm64|s390x|riscv64|ppc64le|loong64|mips64le)"
)


def prune_sqlite_lib(lib: Path) -> int:
    removed = 0
    for path in lib.glob("*.go"):
        if path.name in KEEP_SQLITE:
            continue
        if path.name.startswith("sqlite_") or path.name.startswith("hooks_"):
            path.unlink()
            removed += 1
    return removed


def should_drop(name: str) -> bool:
    if "_linux_amd64" in name:
        return False
    return bool(NON_LINUX_AMD64.search(name))


def prune_libc(libc: Path) -> int:
    removed = 0
    for path in libc.rglob("*.go"):
        if should_drop(path.name):
            path.unlink()
            removed += 1
    return removed


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "vendor" / "modernc.org"
    sqlite_lib = root / "sqlite" / "lib"
    libc = root / "libc"
    n_sqlite = prune_sqlite_lib(sqlite_lib) if sqlite_lib.is_dir() else 0
    n_libc = prune_libc(libc) if libc.is_dir() else 0
    print(f"removed sqlite/lib={n_sqlite} libc={n_libc}")


if __name__ == "__main__":
    main()
