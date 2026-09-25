"""Independent reference checks for ebuild-phase src_install and full runs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

EBUILD = Path("/app/bin/ebuild-phase")
RESET = Path("/app/scripts/reset-state.sh")
LEDGER = Path("/app/state/merge-ledger.json")
TRACE = Path("/app/state/phase-trace.json")


def reset_state() -> None:
    subprocess.run(["bash", str(RESET)], check=True, capture_output=True, text=True)


def package_root() -> Path:
    override = os.environ.get("TB3_PACKAGE_ROOT")
    if override:
        return Path(override)
    return Path("/opt/verifier-fixtures/packages")


def run_src_install(tree: Path, dest: Path) -> subprocess.CompletedProcess[str]:
    dest.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            str(EBUILD),
            "run",
            "--tree",
            str(tree),
            "--d",
            str(dest),
            "--phase",
            "src_install",
        ],
        capture_output=True,
        text=True,
    )


def run_full(tree: Path, dest: Path) -> subprocess.CompletedProcess[str]:
    dest.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [
            str(EBUILD),
            "run",
            "--tree",
            str(tree),
            "--d",
            str(dest),
            "--phase",
            "full",
        ],
        capture_output=True,
        text=True,
    )


def load_trace() -> list[str]:
    data = json.loads(TRACE.read_text(encoding="utf-8"))
    return list(data.get("steps", []))


def reference_trace_ok(steps: list[str], expected_prefix: list[str]) -> bool:
    if len(steps) < len(expected_prefix):
        return False
    return steps[: len(expected_prefix)] == expected_prefix


def symlink_resolves_inside(dest: Path, link: Path) -> bool:
    if not link.is_symlink():
        return False
    target = os.path.normpath((link.parent / os.readlink(link)).resolve())
    dest_root = dest.resolve()
    return str(target).startswith(str(dest_root) + os.sep) or target == dest_root


def reference_setuid_ok(dest: Path, relpath: str) -> bool:
    path = dest / relpath
    mode = path.stat().st_mode
    return bool(mode & 0o4000)


def count_dirs_not_0755(dest: Path) -> int:
    count = 0
    for p in dest.rglob("*"):
        if p.is_dir() and (p.stat().st_mode & 0o777) != 0o755:
            count += 1
    return count


def ledger_records() -> list[dict]:
    if not LEDGER.exists():
        return []
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    return list(data.get("records", []))


def ledger_status(package: str) -> str | None:
    matches = [r for r in ledger_records() if r.get("package") == package]
    if not matches:
        return None
    return str(matches[-1].get("status"))
