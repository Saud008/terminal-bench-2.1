#!/usr/bin/env python3
"""First-submit acceptance gate — blocks pack_zip until Phase F′ PASS is recorded.

  python3 scripts/first_submit_pack_gate.py --pack-gate --task-dir tasks/<name>
  python3 scripts/first_submit_pack_gate.py --record --task-dir tasks/<name> \\
    --oracle 1.0 --nop 0.0 \\
    --probe 1=PASS --probe 3=PASS --probe 4=PASS --probe 5=PASS \\
    --probe 1b=PASS --probe 7=PASS --probe 8=PASS

Override (user explicit only): TERMINUS_FIRST_SUBMIT_SKIP=1 ./scripts/pack_zip.sh <name>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

PLATFORM_FILE = REPO_ROOT / "scripts" / "platform_submissions.txt"

PROBE_ALIASES = {
    "1": "1_single_file",
    "1_single_file": "1_single_file",
    "1b": "1b_decoy_only",
    "1b_decoy_only": "1b_decoy_only",
    "2": "2_persistence_omitted",
    "2_persistence_omitted": "2_persistence_omitted",
    "3": "3_hidden_vs_bundled",
    "3_hidden_vs_bundled": "3_hidden_vs_bundled",
    "4": "4_almost_correct_trap",
    "4_almost_correct_trap": "4_almost_correct_trap",
    "5": "5_doc_depth",
    "5_doc_depth": "5_doc_depth",
    "7": "7_staging_artifact",
    "7_staging_artifact": "7_staging_artifact",
    "8": "8_ingest_only_patch",
    "8_ingest_only_patch": "8_ingest_only_patch",
}

REQUIRED_ALL = ("1_single_file", "3_hidden_vs_bundled", "4_almost_correct_trap", "5_doc_depth")
REQUIRED_CLI_EXPORT = ("1b_decoy_only", "7_staging_artifact", "8_ingest_only_patch")


def _slug_from_task_dir(task_dir: Path) -> str:
    return task_dir.resolve().name


def _record_path(slug: str, *, mkdir: bool = False) -> Path:
    return jobs_path(f"first-submit-{slug}.json", mkdir=mkdir)


def _load_platform_slugs() -> set[str]:
    if not PLATFORM_FILE.is_file():
        return set()
    out: set[str] = set()
    for line in PLATFORM_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line.split()[0])
    return out


def _is_milestone(task_dir: Path) -> bool:
    return (task_dir / "steps").is_dir() and (task_dir / "task.toml").is_file()


def _read_toml_languages(task_dir: Path) -> list[str]:
    path = task_dir / "task.toml"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"languages\s*=\s*\[([^\]]+)\]", text, re.I)
    if not m:
        return []
    return [x.strip().strip('"').strip("'").lower() for x in m.group(1).split(",") if x.strip()]


def _is_compile_cli_export(task_dir: Path) -> bool:
    langs = _read_toml_languages(task_dir)
    if not any(x in langs for x in ("go", "rust", "bash", "c", "c++", "cpp")):
        return False
    tests = task_dir / "tests" / "test_outputs.py"
    if not tests.is_file():
        return False
    body = tests.read_text(encoding="utf-8", errors="replace").lower()
    return bool(body) and (
        "export" in body
        or "staging" in body
        or "snapshot" in body
        or "subprocess" in body
        or "/app/bin/" in body
    )


def _needs_persistence_probe(task_dir: Path) -> bool:
    tests = task_dir / "tests" / "test_outputs.py"
    if not tests.is_file():
        return False
    body = tests.read_text(encoding="utf-8", errors="replace").lower()
    keys = ("cross-run", "cross_run", "replay", "idempoten", "sequence", "persist")
    return any(k in body for k in keys)


def _normalize_probe_key(raw: str) -> str:
    key = raw.strip().lower().replace(" ", "_")
    return PROBE_ALIASES.get(key, key)


def _parse_probe_arg(s: str) -> tuple[str, str, str]:
    """1=PASS:evidence or 1=PASS"""
    if "=" not in s:
        raise ValueError(f"bad --probe (need KEY=STATUS): {s}")
    key_part, rest = s.split("=", 1)
    key = _normalize_probe_key(key_part)
    if ":" in rest:
        status, evidence = rest.split(":", 1)
    else:
        status, evidence = rest, ""
    status = status.strip().upper()
    if status not in ("PASS", "FAIL", "N/A"):
        raise ValueError(f"probe status must be PASS/FAIL/N/A: {s}")
    return key, status, evidence.strip()


def _task_difficulty(task_dir: Path) -> str:
    path = task_dir / "task.toml"
    if not path.is_file():
        return "medium"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("difficulty"):
            low = line.lower()
            if "hard" in low:
                return "hard"
            if "easy" in low:
                return "easy"
    return "medium"


def _min_tests(task_dir: Path) -> int:
    return 18 if _task_difficulty(task_dir) == "hard" else 15


def _count_solution_files(task_dir: Path) -> int:
    n = 0
    for sub in ("files", "patches", "fixed"):
        d = task_dir / "solution" / sub
        if d.is_dir():
            n += sum(1 for p in d.rglob("*") if p.is_file())
    return n


def _live_probe_errors(task_dir: Path) -> list[str]:
    """Re-run terminus_auto_probes — blocks stale manual PASS records."""
    try:
        from terminus_auto_probes import run_probes  # noqa: WPS433
    except ImportError:
        return ["terminus_auto_probes.py not importable"]
    errors: list[str] = []
    live = run_probes(task_dir)
    for key in _required_probe_keys(task_dir):
        entry = live.get(key, {})
        if entry.get("status") == "FAIL":
            errors.append(f"live auto-probe {key} FAIL — {entry.get('evidence', '')}")
    return errors


def _required_probe_keys(task_dir: Path) -> list[str]:
    keys = list(REQUIRED_ALL)
    if _is_compile_cli_export(task_dir):
        keys.extend(REQUIRED_CLI_EXPORT)
    if _needs_persistence_probe(task_dir):
        keys.append("2_persistence_omitted")
    return keys


def _validate_record(data: dict, task_dir: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if data.get("verdict") != "PASS":
        errors.append("verdict must be PASS")
    oracle = str(data.get("oracle", "")).strip()
    nop = str(data.get("nop", "")).strip()
    if oracle not in ("1", "1.0", "1.00"):
        errors.append(f"oracle must be 1.0 (got {oracle!r})")
    if nop not in ("0", "0.0", "0.00"):
        errors.append(f"nop must be 0.0 (got {nop!r})")

    probes: dict = data.get("probes") or {}
    if not isinstance(probes, dict):
        errors.append("probes must be an object")
        probes = {}

    for key in _required_probe_keys(task_dir):
        entry = probes.get(key)
        if not entry:
            errors.append(f"missing probe: {key}")
            continue
        if isinstance(entry, str):
            status = entry.upper()
        elif isinstance(entry, dict):
            status = str(entry.get("status", "")).upper()
        else:
            status = ""
        if status == "FAIL":
            errors.append(f"probe {key} is FAIL")
        elif status == "N/A" and key != "2_persistence_omitted":
            errors.append(f"probe {key} cannot be N/A")
        elif status not in ("PASS", "N/A"):
            errors.append(f"probe {key} invalid status {status!r}")

    if _needs_persistence_probe(task_dir):
        entry = probes.get("2_persistence_omitted")
        if entry:
            status = entry.get("status", entry) if isinstance(entry, dict) else entry
            if str(status).upper() not in ("PASS",):
                errors.append("persistence task requires probe 2 PASS")

    # Lightweight structural hints (warn → block on first submit)
    env = task_dir / "environment"
    inst = task_dir / "instruction.md"
    if inst.is_file():
        doc_hits = len(
            re.findall(
                r"/app/(?:docs|contracts|charter)/[^\s\)]+\.md",
                inst.read_text(encoding="utf-8", errors="replace"),
            )
        )
        if doc_hits < 3:
            errors.append(
                f"instruction.md cites {doc_hits} /app/docs, /app/contracts, or /app/charter paths (need ≥3 for probe 5)"
            )

    tests = task_dir / "tests" / "test_outputs.py"
    min_t = _min_tests(task_dir)
    if tests.is_file():
        body = tests.read_text(encoding="utf-8", errors="replace")
        if "reference_" not in body and "def reference" not in body.lower():
            errors.append("tests/test_outputs.py lacks independent reference_* helper")
        test_count = len(re.findall(r"^\s*def test_", body, re.M))
        if test_count < min_t:
            errors.append(
                f"only {test_count} behavioral tests (need ≥{min_t} for difficulty={_task_difficulty(task_dir)})"
            )
        if "subprocess" not in body and "run([" not in body and "Popen(" not in body:
            errors.append("tests must invoke CLI via subprocess (shared/trivial-first-upload-lock.mdc)")

    sol = _count_solution_files(task_dir)
    min_sol = 5 if _task_difficulty(task_dir) == "hard" else 3
    if sol < min_sol:
        errors.append(
            f"solution has {sol} patch files under files/patches/fixed (need ≥{min_sol})"
        )

    if _is_compile_cli_export(task_dir):
        if tests.is_file():
            body = tests.read_text(encoding="utf-8", errors="replace").lower()
            if "snapshot" not in body and "staging" not in body:
                errors.append("ingest/export CLI: no staging/snapshot test in test_outputs.py")

    errors.extend(_live_probe_errors(task_dir))

    return (len(errors) == 0, errors)


def write_report(lines: list[str]) -> None:
    try:
        path = jobs_path("first-submit-last.txt", mkdir=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def cmd_record(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).resolve()
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1
    slug = _slug_from_task_dir(task_dir)
    probes: dict[str, dict[str, str]] = {}
    for raw in args.probe or []:
        key, status, evidence = _parse_probe_arg(raw)
        probes[key] = {"status": status, "evidence": evidence}

    data = {
        "slug": slug,
        "verdict": args.verdict.upper(),
        "oracle": args.oracle,
        "nop": args.nop,
        "probes": probes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "task_dir": str(task_dir.relative_to(REPO_ROOT)) if task_dir.is_relative_to(REPO_ROOT) else str(task_dir),
        "first_submit_risk": args.risk or "",
        "notes": args.notes or "",
    }
    ok, errors = _validate_record(data, task_dir)
    if not ok and data["verdict"] == "PASS":
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print("First-submit record rejected — fix probes/structure then re-run --record", file=sys.stderr)
        return 1

    out = _record_path(slug, mkdir=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"First-submit/templated: {'PASS' if data['verdict'] == 'PASS' else 'FAIL'} — {slug}",
        f"  record: {out.relative_to(REPO_ROOT)}",
    ]
    if errors:
        for e in errors:
            lines.append(f"  warn: {e}")
    write_report(lines)
    print("\n".join(lines))
    return 0 if data["verdict"] == "PASS" and ok else 1


def cmd_pack_gate(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir).resolve()
    slug = _slug_from_task_dir(task_dir)
    lines = [f"First-submit pack gate — {slug}"]

    if _is_milestone(task_dir):
        lines.append("  skip: milestone task (F′ gate applies to non-milestone CREATE)")
        write_report(lines)
        print("\n".join(lines))
        return 0

    platform = _load_platform_slugs()
    if slug in platform:
        lines.append(f"  skip: slug in scripts/platform_submissions.txt (resubmit — use ENGINE_7 REVISE)")
        write_report(lines)
        print("\n".join(lines))
        return 0

    rec = _record_path(slug)
    if not rec.is_file():
        lines.extend(
            [
                "First-submit/templated: FAIL — no Phase F′ record",
                f"  blocker: missing {rec.relative_to(REPO_ROOT)}",
                "  fix: shared/trivial-first-upload-lock.mdc + Case 6 at CREATE:",
                "    python3 scripts/terminus_auto_probes.py --task-dir " + str(task_dir.relative_to(REPO_ROOT)),
                "    ./scripts/create_finish_to_zip.sh " + slug,
                "  override (user explicit only): TERMINUS_FIRST_SUBMIT_SKIP=1 ./scripts/pack_zip.sh " + slug,
            ]
        )
        write_report(lines)
        print("\n".join(lines), file=sys.stderr)
        return 1

    try:
        data = json.loads(rec.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        lines.append(f"First-submit/templated: FAIL — corrupt record: {exc}")
        write_report(lines)
        print("\n".join(lines), file=sys.stderr)
        return 1

    ok, errors = _validate_record(data, task_dir)
    if not ok:
        lines.append("First-submit/templated: FAIL — record invalid or stale")
        for e in errors:
            lines.append(f"  blocker: {e}")
        lines.append(f"  re-record after fixes: python3 scripts/first_submit_pack_gate.py --record --task-dir ...")
        write_report(lines)
        print("\n".join(lines), file=sys.stderr)
        return 1

    lines.append("First-submit/templated: PASS — Phase F′ record OK")
    lines.append(f"  record: {rec.relative_to(REPO_ROOT)}")
    write_report(lines)
    print("\n".join(lines))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="First-submit acceptance gate for pack_zip.sh")
    parser.add_argument("--task-dir", type=Path, help="Path to tasks/<name>/ or pending/<name>/")
    parser.add_argument("--task-name", type=str, help="Task slug (resolved under tasks/ then pending/)")
    parser.add_argument("--pack-gate", action="store_true", help="Exit 1 if first-upload F′ not PASS")
    parser.add_argument("--record", action="store_true", help="Write jobs-local/first-submit-<slug>.json")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--verdict", default="PASS", choices=("PASS", "FAIL"))
    parser.add_argument("--oracle", default="1.0")
    parser.add_argument("--nop", default="0.0")
    parser.add_argument("--risk", default="", help="First-submit risk: Low/Medium/High")
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--probe",
        action="append",
        help="Probe result KEY=PASS|FAIL|N/A[:evidence] (repeat)",
    )
    args = parser.parse_args()

    task_dir = args.task_dir
    if task_dir is None and args.task_name:
        for base in (REPO_ROOT / "tasks", REPO_ROOT / "pending"):
            candidate = base / args.task_name
            if candidate.is_dir():
                task_dir = candidate
                break
    if task_dir is None:
        parser.error("--task-dir or --task-name required")

    if args.record:
        return cmd_record(args)
    if args.pack_gate:
        return cmd_pack_gate(args)

    parser.error("specify --pack-gate or --record")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
