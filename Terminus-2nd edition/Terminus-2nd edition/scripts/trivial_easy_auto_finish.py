#!/usr/bin/env python3
"""TRIVIAL/EASY steps 8–14 — automated (hooks + one command).

Runs in order (no skips):
  8. terminus_auto_probes.py
  9. preupload_agent_calibration.py --record (from jobs-local context or --opus/--gpt)
 10. probe report path (from auto probes JSON)
 11–13. create_finish_to_zip.py (audit → harbor → ruff → F′ → pack_zip)

  python3 scripts/trivial_easy_auto_finish.py --task-name <slug>
  python3 scripts/trivial_easy_auto_finish.py --task-dir tasks/<slug> --hook-mode

Exit 0 only when probes PASS, finish pipeline PASS, and zip exists.
Calibration FAIL (worst >20% HARD target) returns 4 — deepen Case 6; re-run after local smoke --post-harden.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 3700) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT: {' '.join(cmd)}"


def locate_task_dir(name: str, task_dir: Path | None) -> Path | None:
    if task_dir is not None:
        return task_dir.resolve() if task_dir.is_dir() else None
    for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
        candidate = base / name
        if candidate.is_dir() and (candidate / "task.toml").is_file():
            return candidate
    return None


def write_summary(payload: dict) -> Path:
    path = jobs_path("trivial-easy-pipeline-last.json", mkdir=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-name", default="")
    parser.add_argument("--task-dir", type=Path, default=None)
    parser.add_argument("--opus", default="")
    parser.add_argument("--gpt", default="")
    parser.add_argument(
        "--hook-mode",
        action="store_true",
        help="Called from Cursor hook — use harbor cache in finish step",
    )
    parser.add_argument(
        "--skip-calibration",
        action="store_true",
        help="Skip step 9 (debug only)",
    )
    args = parser.parse_args()

    task_dir = locate_task_dir(args.task_name, args.task_dir)
    if not task_dir:
        print("ERROR: task not found", file=sys.stderr)
        return 1
    slug = task_dir.name

    summary: dict = {
        "slug": slug,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
    }

    print(f"=== TRIVIAL/EASY auto pipeline (steps 8–14): {slug} ===\n")

    # Step 8 — probes
    print("--- Step 8: terminus_auto_probes ---")
    probe_script = REPO_ROOT / "scripts" / "terminus_auto_probes.py"
    rc, out = _run(
        [sys.executable, str(probe_script), "--task-dir", str(task_dir)],
        timeout=300,
    )
    summary["steps"]["8_probes"] = {"rc": rc, "tail": out[-3000:]}
    print(out)
    if rc != 0:
        summary["verdict"] = "FAIL_STEP_8_PROBES"
        write_summary(summary)
        print("\nBLOCKED: probes FAIL — Case 6 structural hardening required.", file=sys.stderr)
        return 1

    # Step 9 — agent calibration record
    opus = args.opus
    gpt = args.gpt
    if not opus or not gpt:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from trivial_easy_context import load_context  # noqa: WPS433

        ctx = load_context(slug) or {}
        opus = opus or ctx.get("opus", "")
        gpt = gpt or ctx.get("gpt", "")

    cal_rc = 0
    cal_out = "skipped"
    if not args.skip_calibration and (opus or gpt):
        print("\n--- Step 9: preupload_agent_calibration --record ---")
        cal_script = REPO_ROOT / "scripts" / "preupload_agent_calibration.py"
        cal_cmd = [
            sys.executable,
            str(cal_script),
            "--record",
            "--task-dir",
            str(task_dir),
        ]
        if opus:
            cal_cmd.extend(["--opus", opus])
        if gpt:
            cal_cmd.extend(["--gpt", gpt])
        cal_cmd.append("--post-harden")
        cal_rc, cal_out = _run(cal_cmd, timeout=60)
        summary["steps"]["9_calibration"] = {
            "rc": cal_rc,
            "opus": opus,
            "gpt": gpt,
            "tail": cal_out[-1500:],
        }
        print(cal_out)
        if cal_rc != 0:
            summary["steps"]["9_calibration"]["verdict"] = "FAIL"
            summary["verdict"] = "FAIL_STEP_9_CALIBRATION"
            write_summary(summary)
            print(
                "\nBLOCKED: calibration FAIL (HARD target worst ≤20% + --post-harden after Case 6). "
                "Do not zip until local Opus/GPT smoke re-recorded.",
                file=sys.stderr,
            )
            return 4
        summary["steps"]["9_calibration"]["verdict"] = "PASS"
    else:
        summary["steps"]["9_calibration"] = {"skipped": True}

    # Steps 11–13 — create_finish_to_zip (includes F′ + pack)
    print("\n--- Steps 11–13: create_finish_to_zip ---")
    finish_script = REPO_ROOT / "scripts" / "create_finish_to_zip.py"
    finish_cmd = [
        sys.executable,
        str(finish_script),
        "--task-dir",
        str(task_dir),
    ]
    if args.hook_mode:
        finish_cmd.append("--hook-mode")
    fin_rc, fin_out = _run(finish_cmd, timeout=3700)
    summary["steps"]["11_13_finish"] = {"rc": fin_rc, "tail": fin_out[-4000:]}
    print(fin_out)

    finish_json = resolve_jobs_path("create-finish-last.json")
    if finish_json.is_file():
        try:
            summary["create_finish"] = json.loads(finish_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    if fin_rc != 0:
        summary["verdict"] = "FAIL_STEP_11_13_FINISH"
        write_summary(summary)
        return fin_rc if fin_rc in (2, 3) else 1

    zip_path = REPO_ROOT / "tasksubmit" / f"{slug}.zip"
    summary["verdict"] = "PASS"
    summary["zip"] = str(zip_path) if zip_path.is_file() else ""
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    report = write_summary(summary)

    print(f"\n✓ TRIVIAL/EASY pipeline PASS: {zip_path if zip_path.is_file() else '(see finish report)'}")
    print(f"  Report: {report.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
