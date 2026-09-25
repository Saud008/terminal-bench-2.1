#!/usr/bin/env python3
"""Run Harbor oracle/NOP locally and parse reward (Phase F).

  python3 scripts/terminus_harbor_verify.py --task-dir tasks/<name>
  python3 scripts/terminus_harbor_verify.py --task-dir tasks/<name> --agent nop

Writes jobs-local/harbor-verify-<slug>.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path  # noqa: E402
from migrate_dockerfile_canonical_ecr import ensure_canonical_task  # noqa: E402

MEAN_RE = re.compile(r"Mean:\s*([0-9]+(?:\.[0-9]+)?)", re.I)


def _harbor_cmd() -> list[str] | None:
    for base in (["stb", "harbor"], ["harbor"]):
        try:
            proc = subprocess.run(
                [*base, "--version"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if proc.returncode == 0:
                return base
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def _latest_result_json(task_dir: Path) -> Path | None:
    jobs = task_dir / "jobs"
    if not jobs.is_dir():
        return None
    candidates = sorted(jobs.glob("*/result.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _mean_from_result(path: Path) -> float | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    stats = data.get("stats") or {}
    for eval_block in (stats.get("evals") or {}).values():
        metrics = eval_block.get("metrics") or []
        if metrics and "mean" in metrics[0]:
            return float(metrics[0]["mean"])
    return None


def _parse_mean(stdout: str) -> float | None:
    matches = MEAN_RE.findall(stdout)
    if not matches:
        return None
    return float(matches[-1])


def _harbor_task_dir(task_dir: Path) -> tuple[Path, Path | None]:
    """Use a /tmp copy when the source path has spaces (Docker mount limitation)."""
    if " " not in str(task_dir):
        return task_dir, None
    staging = Path(tempfile.gettempdir()) / task_dir.name
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(task_dir, staging, ignore=shutil.ignore_patterns("jobs", ".ruff_cache"))
    return staging, staging


def run_harbor_agent(task_dir: Path, agent: str, *, force_build: bool = True) -> dict:
    base = _harbor_cmd()
    if not base:
        return {
            "agent": agent,
            "ok": False,
            "reward": None,
            "error": "stb/harbor not on PATH",
            "stdout": "",
            "stderr": "",
        }

    cmd = [*base, "run", "-a", agent, "-p", ".", "--debug"]
    if force_build:
        cmd.append("--force-build")
    if agent == "nop":
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        cmd.extend(["--job-name", f"{task_dir.name}-nop-{ts}"])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(task_dir),
            capture_output=True,
            text=True,
            timeout=3600,
        )
    except subprocess.TimeoutExpired:
        return {
            "agent": agent,
            "ok": False,
            "reward": None,
            "error": "TIMEOUT 3600s",
            "stdout": "",
            "stderr": "",
        }

    out = (proc.stdout or "") + (proc.stderr or "")
    mean = _parse_mean(out)
    result_path = _latest_result_json(task_dir)
    if mean is None and result_path:
        mean = _mean_from_result(result_path)

    reward = mean
    ok = reward is not None and (
        (agent == "oracle" and reward >= 0.999) or (agent == "nop" and reward <= 0.001)
    )

    return {
        "agent": agent,
        "ok": ok,
        "reward": reward,
        "error": "" if ok else f"expected {'1.0' if agent == 'oracle' else '0.0'}, got {reward}",
        "command": " ".join(cmd),
        "result_json": str(result_path) if result_path else "",
        "stdout_tail": out[-8000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--agent", choices=("oracle", "nop", "both"), default="both")
    parser.add_argument("--no-force-build", action="store_true")
    args = parser.parse_args()

    task_dir = args.task_dir.resolve()
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1

    slug = task_dir.name
    force = not args.no_force_build
    agents = ["oracle", "nop"] if args.agent == "both" else [args.agent]

    ecr_rc = ensure_canonical_task(task_dir, quiet=False)
    if ecr_rc != 0:
        print(
            "ERROR: canonical ECR FROM required before harbor build "
            "(migrate_dockerfile_canonical_ecr.py --ensure)",
            file=sys.stderr,
        )
        return 1

    results: dict[str, dict] = {}
    harbor_dir, staging = _harbor_task_dir(task_dir)

    try:
        for agent in agents:
            results[agent] = run_harbor_agent(harbor_dir, agent, force_build=force)
    finally:
        if staging is not None and staging.is_dir():
            shutil.rmtree(staging, ignore_errors=True)

    payload = {
        "slug": slug,
        "task_dir": str(task_dir),
        "harbor_task_dir": str(harbor_dir),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "oracle": results.get("oracle", {}).get("reward"),
        "nop": results.get("nop", {}).get("reward"),
        "verdict": "PASS"
        if all(results.get(a, {}).get("ok") for a in agents)
        else "FAIL",
    }

    out_path = jobs_path(f"harbor-verify-{slug}.json", mkdir=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"Harbor verify — {slug} — {payload['verdict']}",
        f"  oracle: {payload.get('oracle')} ({'OK' if results.get('oracle', {}).get('ok') else 'FAIL'})",
        f"  nop: {payload.get('nop')} ({'OK' if results.get('nop', {}).get('ok') else 'FAIL'})",
        f"  report: {out_path.relative_to(REPO_ROOT)}",
    ]
    for agent in agents:
        r = results[agent]
        if not r.get("ok") and r.get("error"):
            lines.append(f"  {agent} error: {r['error']}")
    print("\n".join(lines))

    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
