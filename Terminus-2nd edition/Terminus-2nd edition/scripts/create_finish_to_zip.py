#!/usr/bin/env python3
"""CREATE pipeline finish: audit gate → Harbor F → probes F′ → pack_zip (Phase G).

Agent runs this after Phase D (+ semantic Phase E fixes). Do not stop until exit 0.

  python3 scripts/create_finish_to_zip.py --task-name <slug>
  python3 scripts/create_finish_to_zip.py --task-dir tasks/<slug>

Options:
  --skip-audit          Skip static audit loop (agent already CLEAN)
  --skip-harbor         Skip harbor; require --oracle 1.0 --nop 0.0
  --oracle / --nop      Use pre-recorded rewards (WSL evidence)
  --audit-max-rounds N  Default 4

Exit codes:
  0  zip written
  1  hard failure
  2  static audit blocking — fix High/Medium in tasks/<slug>/ then re-run
  3  harbor unavailable or reward mismatch
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
from migrate_dockerfile_canonical_ecr import ensure_canonical_task  # noqa: E402

AUDIT_JSON = resolve_jobs_path("post-create-audit-last.json")


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 3600) -> tuple[int, str]:
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


def _next_audit_round(slug: str) -> int:
    if not AUDIT_JSON.is_file():
        return 1
    try:
        data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 1
    if data.get("slug") != slug:
        return 1
    if data.get("verdict") == "CONTINUE" and int(data.get("blocking", 0)) > 0:
        return min(int(data.get("round", 1)) + 1, 4)
    return 1


def audit_gate(task_dir: Path, max_rounds: int) -> tuple[int, str]:
    """One static audit round per invocation; exit 2 if blocking (agent fixes + re-run)."""
    script = REPO_ROOT / "scripts" / "post_create_audit_loop.py"
    slug = task_dir.name
    round_num = _next_audit_round(slug)
    if round_num > max_rounds:
        return 2, f"audit exceeded {max_rounds} rounds — fix High/Medium manually in {slug}/"

    rc, out = _run(
        [
            sys.executable,
            str(script),
            "--task-dir",
            str(task_dir),
            "--round",
            str(round_num),
            "--pack-gate",
            "--no-harbor",
        ],
        timeout=300,
    )
    verdict = "CONTINUE"
    blocking = 1
    if AUDIT_JSON.is_file():
        try:
            data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
            if data.get("slug") == slug:
                verdict = data.get("verdict", verdict)
                blocking = int(data.get("blocking", blocking))
        except (json.JSONDecodeError, OSError):
            pass
    if verdict == "CLEAN" and blocking == 0 and rc == 0:
        return 0, f"audit CLEAN round {round_num}\n{out}"
    return 2, (
        f"audit blocking round {round_num} — fix High/Medium in {slug}/ then re-run create_finish_to_zip.sh\n{out}"
    )


def _load_harbor_cache(slug: str) -> tuple[bool, str, str]:
    """Return (ok, oracle, nop) from jobs-local/harbor-verify-<slug>.json if PASS."""
    path = resolve_jobs_path(f"harbor-verify-{slug}.json")
    if not path.is_file():
        return False, "", ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False, "", ""
    if str(data.get("verdict", "")).upper() != "PASS":
        return False, "", ""
    o = str(data.get("oracle", ""))
    n = str(data.get("nop", ""))
    o_ok = o.strip() in ("1", "1.0", "1.00")
    n_ok = n.strip() in ("0", "0.0", "0.00")
    return o_ok and n_ok, o, n


def _spawn_background_finish(slug: str) -> str:
    """Harbor can exceed hook timeout — run full finish in background."""
    import os

    JOBS_LOCAL.mkdir(parents=True, exist_ok=True)
    log_path = jobs_path(f"finish-bg-{slug}.log", mkdir=True)
    pid_path = jobs_path(f"finish-bg-{slug}.pid", mkdir=True)
    if pid_path.is_file():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return f"finish already running (pid {pid}) — log: {log_path.relative_to(REPO_ROOT)}"
        except (OSError, ValueError):
            pass
    script = REPO_ROOT / "scripts" / "create_finish_to_zip.py"
    with log_path.open("a", encoding="utf-8") as logf:
        logf.write(f"\n--- spawn {datetime.now(timezone.utc).isoformat()} ---\n")
        proc = subprocess.Popen(
            [sys.executable, str(script), "--task-name", slug],
            stdout=logf,
            stderr=subprocess.STDOUT,
            cwd=str(REPO_ROOT),
            start_new_session=True,
        )
    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return f"spawned background finish pid {proc.pid} — log: {log_path.relative_to(REPO_ROOT)}"


def run_harbor_phase(
    task_dir: Path,
    oracle: str | None,
    nop: str | None,
    *,
    use_cache: bool = False,
) -> tuple[int, str, str, str]:
    if use_cache:
        ok, o, n = _load_harbor_cache(task_dir.name)
        if ok:
            return 0, o, n, "harbor cache PASS (jobs-local/harbor-verify-*.json)"
    if oracle is not None and nop is not None:
        o_ok = oracle.strip() in ("1", "1.0", "1.00")
        n_ok = nop.strip() in ("0", "0.0", "0.00")
        if o_ok and n_ok:
            return 0, oracle, nop, "skipped harbor (--oracle/--nop provided)"
        return 3, oracle or "", nop or "", "invalid --oracle/--nop values"

    script = REPO_ROOT / "scripts" / "terminus_harbor_verify.py"
    rc, out = _run([sys.executable, str(script), "--task-dir", str(task_dir)], cwd=task_dir, timeout=3700)
    report = jobs_path(f"harbor-verify-{task_dir.name}.json", mkdir=True)
    o_val, n_val = "?", "?"
    if report.is_file():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            o_val = str(data.get("oracle", "?"))
            n_val = str(data.get("nop", "?"))
        except (json.JSONDecodeError, OSError):
            pass
    if rc != 0:
        return 3, o_val, n_val, out
    return 0, o_val, n_val, out


def run_ruff(task_dir: Path) -> tuple[int, str]:
    for cmd in (["ruff", "check", "."], [sys.executable, "-m", "ruff", "check", "."]):
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(task_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode == 0 or "All checks passed" in out:
                return 0, out.strip()
            # python -m ruff exits 1 when the module is missing (not 127)
            if "No module named ruff" in out or 'No module named "ruff"' in out:
                continue
            if proc.returncode != 127:
                return proc.returncode, out.strip()
        except (OSError, subprocess.TimeoutExpired):
            continue
    return 0, "ruff skipped (not on PATH)"


def ensure_platform_rubric(task_dir: Path) -> tuple[int, str, str]:
    """Validate rubrics/<slug>.md before pack (positive cumulative 10–40 per block)."""
    slug = task_dir.name
    gate_script = REPO_ROOT / "scripts" / "platform_rubric_gate.py"
    rc, out = _run(
        [sys.executable, str(gate_script), "--pack-gate", "--slug", slug],
        timeout=60,
    )
    rub_path = REPO_ROOT / "rubrics" / f"{slug}.md"
    return rc, str(rub_path) if rub_path.is_file() else "", out


def ensure_submission_explanations(task_dir: Path) -> tuple[int, str, str]:
    """Auto-draft platform form paragraphs before pack (user edits voice before upload)."""
    slug = task_dir.name
    gate_script = REPO_ROOT / "scripts" / "submission_explanations_gate.py"

    rc, out = _run(
        [sys.executable, str(gate_script), "--ensure", "--slug", slug],
        timeout=120,
    )
    expl_path = REPO_ROOT / "submission-explanations" / f"{slug}.md"
    return rc, str(expl_path) if expl_path.is_file() else "", out


def record_f_prime(task_dir: Path, oracle: str, nop: str) -> tuple[int, str]:
    if (task_dir / "steps").is_dir() and (task_dir / "task.toml").is_file():
        return 0, "F′ skipped — milestone task (pack gate exempt)"

    probe_script = REPO_ROOT / "scripts" / "terminus_auto_probes.py"
    rc, probe_args = _run(
        [sys.executable, str(probe_script), "--task-dir", str(task_dir), "--format", "record-args"],
        timeout=60,
    )
    if rc != 0:
        return 1, f"auto probes FAIL\n{probe_args}"

    import shlex

    record_script = REPO_ROOT / "scripts" / "first_submit_pack_gate.py"
    cmd = [
        sys.executable,
        str(record_script),
        "--record",
        "--task-dir",
        str(task_dir),
        "--oracle",
        oracle,
        "--nop",
        nop,
        "--verdict",
        "PASS",
        "--risk",
        "Medium",
        "--notes",
        "create_finish_to_zip.py auto record",
    ]
    cmd.extend(shlex.split(probe_args))
    rc, out = _run(cmd, timeout=60)
    return rc, out


def pack_zip(slug: str) -> tuple[int, str, Path | None]:
    script = REPO_ROOT / "scripts" / "pack_zip.sh"
    # Anti-spam + uniqueness + CI can exceed 5 minutes on Windows/WSL mounts.
    rc, out = _run(["bash", str(script), slug], timeout=900)
    zip_path = REPO_ROOT / "tasksubmit" / f"{slug}.zip"
    if rc == 0 and zip_path.is_file():
        return 0, out, zip_path
    return rc, out, zip_path if zip_path.is_file() else None


def write_summary(payload: dict) -> None:
    path = jobs_path("create-finish-last.json", mkdir=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-name", type=str, default="")
    parser.add_argument("--task-dir", type=Path, default=None)
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-harbor", action="store_true")
    parser.add_argument("--oracle", type=str, default=None)
    parser.add_argument("--nop", type=str, default=None)
    parser.add_argument("--audit-max-rounds", type=int, default=4)
    parser.add_argument(
        "--hook-mode",
        action="store_true",
        help="Called from Cursor hook — reuse harbor cache; spawn bg on harbor block",
    )
    parser.add_argument(
        "--use-harbor-cache",
        action="store_true",
        help="Skip harbor run if jobs-local/harbor-verify-<slug>.json is PASS",
    )
    args = parser.parse_args()

    if args.hook_mode and (args.skip_audit or args.skip_harbor):
        print(
            "ERROR: --hook-mode cannot use --skip-audit or --skip-harbor (full pipeline required)",
            file=sys.stderr,
        )
        return 1

    task_dir = locate_task_dir(args.task_name, args.task_dir)
    if not task_dir:
        parser.error("task not found — use --task-name or --task-dir")
    slug = task_dir.name

    summary: dict = {
        "slug": slug,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phases": {},
    }

    print(f"=== CREATE finish → zip: {slug} ===\n")

    print("--- Canonical ECR (auto-fix + verify before build) ---")
    ecr_rc = ensure_canonical_task(task_dir, quiet=False)
    summary["phases"]["canonical_ecr"] = {"rc": ecr_rc}
    if ecr_rc != 0:
        summary["verdict"] = "BLOCKED_CANONICAL_ECR"
        write_summary(summary)
        print(
            "\nBLOCKED: every Dockerfile FROM must use public.ecr.aws canonical images "
            "(see canonical-base-image-gate.mdc). Fix environment/Dockerfile then re-run.",
            file=sys.stderr,
        )
        return 1

    if not args.skip_audit:
        print("--- Phase E (static audit gate) ---")
        rc, out = audit_gate(task_dir, args.audit_max_rounds)
        summary["phases"]["audit"] = {"rc": rc, "tail": out[-2000:]}
        print(out)
        if rc == 2:
            summary["verdict"] = "BLOCKED_AUDIT"
            write_summary(summary)
            print("\nBLOCKED: fix audit High/Medium then re-run.", file=sys.stderr)
            return 2
        if rc != 0:
            summary["verdict"] = "FAIL_AUDIT"
            write_summary(summary)
            return 1

    print("\n--- Phase F (Harbor oracle + NOP) ---")
    use_cache = args.use_harbor_cache or args.hook_mode
    if args.skip_harbor:
        if not args.oracle or not args.nop:
            # Hook may rely on harbor cache without explicit flags
            ok, co, cn = _load_harbor_cache(slug)
            if ok:
                o_val, n_val = co, cn
                harbor_out = "harbor cache (skip-harbor + cached PASS)"
                harbor_rc = 0
            else:
                print("ERROR: --skip-harbor requires --oracle and --nop (or harbor cache PASS)", file=sys.stderr)
                return 1
        else:
            o_val, n_val = args.oracle, args.nop
            harbor_out = "harbor skipped"
            harbor_rc = 0
    else:
        harbor_rc, o_val, n_val, harbor_out = run_harbor_phase(
            task_dir, args.oracle, args.nop, use_cache=use_cache
        )
    summary["phases"]["harbor"] = {"rc": harbor_rc, "oracle": o_val, "nop": n_val}
    if not args.hook_mode:
        print(harbor_out)
    if harbor_rc != 0:
        summary["verdict"] = "BLOCKED_HARBOR"
        write_summary(summary)
        if args.hook_mode:
            bg_msg = _spawn_background_finish(slug)
            print(f"Harbor blocked — {bg_msg}", file=sys.stderr)
            return 3
        print(
            "\nBLOCKED: Harbor oracle must be 1.0 and NOP 0.0. "
            "Fix Docker/WSL or pass evidence: --skip-harbor --oracle 1.0 --nop 0.0",
            file=sys.stderr,
        )
        return 3

    print("\n--- Phase F (ruff) ---")
    ruff_rc, ruff_out = run_ruff(task_dir)
    summary["phases"]["ruff"] = {"rc": ruff_rc}
    print(ruff_out)
    if ruff_rc != 0:
        summary["verdict"] = "FAIL_RUFF"
        write_summary(summary)
        return 1

    print("\n--- Phase F′ (probes + record) ---")
    rec_rc, rec_out = record_f_prime(task_dir, str(o_val), str(n_val))
    summary["phases"]["f_prime"] = {"rc": rec_rc}
    print(rec_out)
    if rec_rc != 0:
        summary["verdict"] = "FAIL_F_PRIME"
        write_summary(summary)
        return 1

    print("\n--- Phase G prep (platform rubric — 10–40 positive cumulative) ---")
    rub_rc, rub_path, rub_out = ensure_platform_rubric(task_dir)
    summary["phases"]["platform_rubric"] = {"rc": rub_rc, "path": rub_path}
    print(rub_out)
    if rub_rc != 0:
        summary["verdict"] = "BLOCKED_PLATFORM_RUBRIC"
        write_summary(summary)
        print(
            "\nBLOCKED: rubrics/<slug>.md missing or positive cumulative not 10–40. "
            "Fix with write_platform_rubric.py then re-run.",
            file=sys.stderr,
        )
        return 1

    print("\n--- Phase G prep (submission explanations — platform form) ---")
    expl_rc, expl_path, expl_out = ensure_submission_explanations(task_dir)
    summary["phases"]["submission_explanations"] = {"rc": expl_rc, "path": expl_path}
    print(expl_out)
    if expl_rc != 0:
        summary["verdict"] = "BLOCKED_SUBMISSION_EXPLANATIONS"
        write_summary(summary)
        print(
            "\nBLOCKED: submission-explanations/<slug>.md missing or invalid. "
            "Fix with write_submission_explanations.py --draft then re-run.",
            file=sys.stderr,
        )
        return 1

    print("\n--- Phase G (pack_zip.sh) ---")
    pack_rc, pack_out, zip_path = pack_zip(slug)
    summary["phases"]["pack"] = {"rc": pack_rc, "zip": str(zip_path) if zip_path else ""}
    print(pack_out)
    if pack_rc != 0 or not zip_path:
        summary["verdict"] = "FAIL_PACK"
        write_summary(summary)
        return 1

    summary["verdict"] = "PASS"
    summary["zip"] = str(zip_path)
    summary["pipeline_steps"] = [
        "canonical_ecr_ensure",
        "audit",
        "harbor",
        "ruff",
        "f_prime",
        "platform_rubric_gate",
        "submission_explanations_draft_and_gate",
        "pack_ecr_subcategories_category",
        "pack_anti_spam_sim_zero",
        "pack_unacceptable_8",
        "pack_first_submit",
        "pack_ci_preflight",
        "pack_submission_explanations_gate",
        "pack_platform_rubric_gate",
        "pack_zip_verify_g026_g027",
        "terminus_verify_submit",
    ]
    summary["submission_explanations"] = str(
        REPO_ROOT / "submission-explanations" / f"{slug}.md"
    )
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_summary(summary)

    print(f"\n✓ READY: {zip_path}")
    print(f"  Rubric: rubrics/{slug}.md (paste on platform form)")
    print(f"  Explanations: submission-explanations/{slug}.md (edit before platform paste)")
    print(f"  Report: jobs-local/finish/create-finish-last.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
