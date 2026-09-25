#!/usr/bin/env python3
"""Block zip when task shape predicts platform TRIVIAL/EASY (structural depth).

Runs on every pack (first upload + revise). Complements auto-probes and agent calibration.

  python3 scripts/preupload_trivial_shape_gate.py --pack-gate --task-dir tasks/<name>

Override (user explicit only): TERMINUS_TRIVIAL_SHAPE_SKIP=1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

PLATFORM_FILE = REPO_ROOT / "scripts" / "platform_submissions.txt"


def _slug(task_dir: Path) -> str:
    return task_dir.resolve().name


def _platform_slugs() -> set[str]:
    if not PLATFORM_FILE.is_file():
        return set()
    out: set[str] = set()
    for line in PLATFORM_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.split()[0])
    return out


def _read_difficulty(task_dir: Path) -> str:
    path = task_dir / "task.toml"
    if not path.is_file():
        return ""
    m = re.search(r'^\s*difficulty\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip().lower() if m else ""


def _combined_test_body(task_dir: Path) -> str:
    parts: list[str] = []
    top = task_dir / "tests" / "test_outputs.py"
    if top.is_file():
        parts.append(top.read_text(encoding="utf-8", errors="replace"))
    steps = task_dir / "steps"
    if steps.is_dir():
        for tf in sorted(steps.glob("milestone_*/tests/test_*.py")):
            parts.append(tf.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _env_module_count(task_dir: Path) -> int:
    env = task_dir / "environment"
    if not env.is_dir():
        return 0
    exts = {".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".ts", ".js", ".java", ".py", ".sh"}
    skip = {"vendor", "node_modules", ".git", "__pycache__", "target", "dist", "build"}
    parents: set[Path] = set()
    for p in env.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(s in p.parts for s in skip):
            continue
        parents.add(p.parent)
    return len(parents)


def _count_solution_files(task_dir: Path) -> int:
    n = 0
    for sub in ("files", "patches", "fixed"):
        d = task_dir / "solution" / sub
        if d.is_dir():
            n += sum(1 for p in d.rglob("*") if p.is_file())
    return n


def _test_count(task_dir: Path) -> int:
    return len(re.findall(r"^\s*def test_", _combined_test_body(task_dir), re.M))


def _hidden_trap_test_count(task_dir: Path) -> int:
    """Tests whose body references verifier-only fixtures (independent traps)."""
    body = _combined_test_body(task_dir)
    if not body:
        return 0
    count = 0
    chunks = re.split(r"(?=^\s*def test_)", body, flags=re.M)
    for chunk in chunks:
        if not chunk.strip().startswith("def test_"):
            continue
        if re.search(
            r"verifier-fixtures|TB3_[A-Z0-9_]+|/opt/verifier",
            chunk,
            re.I,
        ):
            count += 1
    return count


def _auto_probes_verdict(slug: str) -> tuple[str | None, str]:
    path = resolve_jobs_path(f"auto-probes-{slug}.json")
    if not path.is_file():
        return None, "missing auto-probes JSON"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"unreadable auto-probes: {exc}"
    return str(data.get("verdict", "")).upper() or None, path.name


def _skip_pack_gates(slug: str) -> bool:
    """Only skip when platform slug with no EASY/TRIVIAL revise context."""
    if slug not in _platform_slugs():
        return False
    ctx_path = resolve_jobs_path(f"trivial-easy-context-{slug}.json")
    if not ctx_path.is_file():
        return True
    try:
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    return ctx.get("difficulty") not in ("EASY", "TRIVIAL")


def run_checks(task_dir: Path) -> list[str]:
    failures: list[str] = []
    slug = _slug(task_dir)
    diff = _read_difficulty(task_dir)
    modules = _env_module_count(task_dir)
    tests_n = _test_count(task_dir)
    hidden_tests = _hidden_trap_test_count(task_dir)
    sol_n = _count_solution_files(task_dir)
    min_tests = 18 if diff == "hard" else 15
    min_sol = 5 if diff == "hard" else 3
    min_modules = 5
    min_hidden_tests = 2

    # S1 — metadata: first uploads must target HARD band
    if diff != "hard":
        failures.append(
            f'S1 difficulty={diff!r} — upload only difficulty = "hard" '
            "(medium/easy metadata → platform EASY even when oracle passes)"
        )

    # S2 — module depth (no one-file pipeline)
    if modules < min_modules:
        failures.append(
            f"S2 env source dirs={modules} (need ≥{min_modules} distinct modules) — "
            "Case 6 ingest/staging/export/decoy/persist split"
        )

    # S3 — behavioral test count
    if tests_n < min_tests:
        failures.append(
            f"S3 behavioral tests={tests_n} (need ≥{min_tests} for difficulty={diff or 'unknown'})"
        )

    # S4 — independent hidden traps (not bundled duplicate)
    if hidden_tests < min_hidden_tests:
        failures.append(
            f"S4 hidden-trap tests={hidden_tests} (need ≥{min_hidden_tests} tests using "
            "/opt/verifier-fixtures or TB3_* — different failure mode than bundled)"
        )

    # S5 — oracle patches enough layers
    if sol_n < min_sol:
        failures.append(
            f"S5 solution patch files={sol_n} (need ≥{min_sol} under solution/files|patches|fixed)"
        )

    # S6 — auto-probes must be PASS on disk (pack runs live re-check via F′)
    verdict, probe_note = _auto_probes_verdict(slug)
    if verdict != "PASS":
        failures.append(
            f"S6 auto-probes verdict={verdict!r} ({probe_note}) — "
            "run: python3 scripts/terminus_auto_probes.py --task-dir "
            + str(task_dir.relative_to(REPO_ROOT))
        )
    else:
        try:
            from terminus_auto_probes import run_probes  # noqa: WPS433

            live = run_probes(task_dir)
            live_fails = [k for k, v in live.items() if v.get("status") == "FAIL"]
            if live_fails:
                failures.append(
                    f"S6 live auto-probes FAIL: {', '.join(live_fails)} — "
                    "structural depth insufficient for Opus/GPT ≤20%"
                )
        except ImportError:
            failures.append("S6 cannot import terminus_auto_probes for live re-check")

    # S7 — platform EASY context: require post-harden agent smoke
    ctx_path = resolve_jobs_path(f"trivial-easy-context-{slug}.json")
    smoke_path = resolve_jobs_path(f"agent-smoke-{slug}.json")
    if ctx_path.is_file():
        try:
            ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            ctx = {}
        if ctx.get("difficulty") in ("EASY", "TRIVIAL"):
            smoke: dict | None = None
            if smoke_path.is_file():
                try:
                    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    smoke = None
            if not smoke or not smoke.get("post_harden"):
                failures.append(
                    f"S7 platform {ctx['difficulty']} on record — Case 6 + local Opus/GPT smoke "
                    "with worst ≤20%, then preupload_agent_calibration.py --record --post-harden"
                )
            elif float(smoke.get("worst_rate", 1.0)) > 0.20:
                failures.append(
                    f"S7 post-harden worst_rate={smoke.get('worst_rate')} > 20% — "
                    "deeper traps required before zip"
                )

    return failures


def cmd_pack_gate(args: argparse.Namespace) -> int:
    if os.environ.get("TERMINUS_TRIVIAL_SHAPE_SKIP") == "1":
        print("SKIP trivial shape gate (TERMINUS_TRIVIAL_SHAPE_SKIP=1)")
        return 0

    task_dir = Path(args.task_dir).resolve()
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1

    slug = _slug(task_dir)
    if _skip_pack_gates(slug):
        print(f"SKIP trivial shape gate — {slug} on platform, no EASY/TRIVIAL revise context")
        return 0

    failures = run_checks(task_dir)
    report_path = jobs_path("trivial-shape-last.txt", mkdir=True)
    lines = [
        f"slug: {slug}",
        f"task_dir: {task_dir}",
        f"checked_at: {datetime.now(timezone.utc).isoformat()}",
        f"verdict: {'PASS' if not failures else 'FAIL'}",
    ]
    if failures:
        lines.append("failures:")
        lines.extend(f"  - {f}" for f in failures)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if failures:
        print("FAIL trivial shape gate — platform would likely label EASY/TRIVIAL:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"  Policy: shared/block-trivial-platform-acceptance.mdc", file=sys.stderr)
        print(f"  Details: {report_path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1

    print("PASS trivial shape gate — structural depth OK for HARD target")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--pack-gate", action="store_true")
    args = parser.parse_args()
    if not args.pack_gate:
        parser.error("use --pack-gate")
    return cmd_pack_gate(args)


if __name__ == "__main__":
    raise SystemExit(main())
