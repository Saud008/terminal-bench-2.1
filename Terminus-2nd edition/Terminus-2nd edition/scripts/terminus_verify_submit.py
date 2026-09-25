#!/usr/bin/env python3
"""Pre-submit verifier — G-025–G-027 + Snorkel CI static checks + Phase F′ (automated).

User does not run checks manually; pack_zip.sh and hooks call this script.

Phase F′ (first upload): calls first_submit_pack_gate.py — same hard block as pack_zip.sh
(no zip / no PASS until jobs-local/first-submit-<slug>.json). Skips: milestone tasks;
slug in scripts/platform_submissions.txt. Override: TERMINUS_FIRST_SUBMIT_SKIP=1.

Usage:
  python3 scripts/terminus_verify_submit.py --task-dir tasks/<name>
  python3 scripts/terminus_verify_submit.py --task-dir tasks/<name> --zip tasksubmit/<name>.zip
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_ci(task_dir: Path, *, pack_gate: bool) -> int:
    script = REPO_ROOT / "scripts" / "terminus_preflight.py"
    cmd = [sys.executable, str(script), "--task-dir", str(task_dir)]
    if pack_gate:
        cmd.append("--pack-gate")
    return subprocess.call(cmd, cwd=str(REPO_ROOT))


def _run_first_submit_gate(task_dir: Path) -> int:
    """Phase F′ — same gate as pack_zip.sh (first upload only)."""
    if os.environ.get("TERMINUS_FIRST_SUBMIT_SKIP", "0") == "1":
        print("SKIP first-submit F′ gate (TERMINUS_FIRST_SUBMIT_SKIP=1)")
        return 0
    script = REPO_ROOT / "scripts" / "first_submit_pack_gate.py"
    cmd = [
        sys.executable,
        str(script),
        "--pack-gate",
        "--quiet",
        "--task-dir",
        str(task_dir.resolve()),
    ]
    code = subprocess.call(cmd, cwd=str(REPO_ROOT))
    if code != 0:
        print(
            "ERROR: First-submit acceptance gate failed (Phase F′ — create/first-submit-acceptance-gate.mdc)",
            file=sys.stderr,
        )
        print("       Details: jobs-local/first-submit-last.txt", file=sys.stderr)
        print(
            "       Record PASS: python3 scripts/first_submit_pack_gate.py --record --task-dir "
            f"{task_dir.relative_to(REPO_ROOT) if task_dir.is_relative_to(REPO_ROOT) else task_dir} "
            "--oracle 1.0 --nop 0.0 --probe 1=PASS ...",
            file=sys.stderr,
        )
    return code


def _check_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []
    if not zip_path.is_file():
        return [f"zip missing: {zip_path}"]

    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        return [f"not a valid zip: {zip_path}"]

    if not any(n == "tests/test_outputs.py" for n in names):
        if not any(n.startswith("steps/") for n in names):
            errors.append("G-026: zip missing tests/test_outputs.py at archive root")

    backslash = [n for n in names if "\\" in n]
    if backslash:
        errors.append(f"G-027: backslash paths in zip: {backslash[:3]}")

    for req in ("task.toml", "environment/Dockerfile"):
        if not any(n == req for n in names):
            errors.append(f"zip missing flat-root {req}")

    if len(names) > 0 and all(n.startswith(f"{zip_path.stem}/") for n in names if "/" in n):
        errors.append(f"nested folder {zip_path.stem}/ at zip root (G-027)")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--zip", dest="zip_path", default="", help="Optional tasksubmit/<name>.zip")
    parser.add_argument("--pack-gate", action="store_true", help="Exit 1 on any blocker")
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / task_dir

    code = _run_ci(task_dir.resolve(), pack_gate=args.pack_gate)
    if code != 0:
        return code

    code = _run_first_submit_gate(task_dir.resolve())
    if code != 0:
        return code

    if args.zip_path:
        zp = Path(args.zip_path)
        if not zp.is_absolute():
            zp = REPO_ROOT / zp
        errs = _check_zip(zp)
        if errs:
            for e in errs:
                print(f"ERROR: {e}", file=sys.stderr)
            return 1
        print(f"OK zip: {zp}")

    print("terminus_verify_submit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
