#!/usr/bin/env python3
"""Structural Phase F′ probes (heuristic — agent may deepen with docker patch tests).

  python3 scripts/terminus_auto_probes.py --task-dir tasks/<name>
  python3 scripts/terminus_auto_probes.py --task-dir tasks/<name> --format record-args

Writes jobs-local/auto-probes-<slug>.json
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
from jobs_local_paths import jobs_path  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from first_submit_pack_gate import (  # noqa: E402
    _is_compile_cli_export,
    _needs_persistence_probe,
    _required_probe_keys,
)


def _step_test_py_files(task_dir: Path) -> list[Path]:
    steps = task_dir / "steps"
    if not steps.is_dir():
        return []
    files: list[Path] = []
    for step_tests in sorted(steps.glob("milestone_*/tests")):
        files.extend(step_tests.glob("test_*.py"))
    return files


def _combined_test_body(task_dir: Path) -> str:
    parts: list[str] = []
    top = task_dir / "tests" / "test_outputs.py"
    if top.is_file():
        parts.append(top.read_text(encoding="utf-8", errors="replace"))
    for tf in _step_test_py_files(task_dir):
        parts.append(tf.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _count_docs_in_instruction(task_dir: Path) -> int:
    total = 0
    inst = task_dir / "instruction.md"
    if inst.is_file():
        total += len(re.findall(r"/app/docs/[^\s\)]+\.md", inst.read_text(encoding="utf-8", errors="replace")))
    steps = task_dir / "steps"
    if steps.is_dir():
        for step_inst in sorted(steps.glob("milestone_*/instruction.md")):
            total += len(
                re.findall(
                    r"/app/docs/[^\s\)]+\.md",
                    step_inst.read_text(encoding="utf-8", errors="replace"),
                )
            )
    return total


def _env_source_file_count(task_dir: Path) -> int:
    env = task_dir / "environment"
    if not env.is_dir():
        return 0
    exts = {".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".ts", ".js", ".java", ".py", ".sh", ".lua", ".sql"}
    skip = {"vendor", "node_modules", ".git", "__pycache__", "target", "dist", "build"}
    n = 0
    for p in env.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(s in p.parts for s in skip):
            continue
        n += 1
    return n


def _env_module_count(task_dir: Path) -> int:
    """Distinct source directories under environment/ (proxy for module depth)."""
    env = task_dir / "environment"
    if not env.is_dir():
        return 0
    exts = {".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".ts", ".js", ".java", ".py", ".sh", ".lua", ".sql"}
    skip = {"vendor", "node_modules", ".git", "__pycache__", "target", "dist", "build"}
    parents: set[Path] = set()
    for p in env.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(s in p.parts for s in skip):
            continue
        parents.add(p.parent)
    return len(parents)


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


def _tests_use_subprocess(task_dir: Path) -> bool:
    body = _combined_test_body(task_dir)
    return "subprocess" in body or "Popen(" in body or "run([" in body


def _test_sh_rebuilds(task_dir: Path) -> bool:
    """True when verifier rebuilds compiled agent code before or during pytest.

    Accept rebuild in tests/test.sh (legacy) or pytest fixtures / test helpers
    (conftest.py, test_outputs.py) so test.sh can stay reward-only.
    """
    tests = task_dir / "tests"
    if not tests.is_dir():
        return False
    needles = ("cargo build", "go build", "npm run build", "rebuild-", " make", "cmake")
    candidates = [
        tests / "test.sh",
        tests / "conftest.py",
        tests / "test_outputs.py",
        *sorted(tests.glob("verifier-rebuild*")),
    ]
    for path in candidates:
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(x in body for x in needles):
            return True
    return False


def _has_hidden_fixtures(task_dir: Path) -> bool:
    body = _combined_test_body(task_dir)
    if body and ("verifier-fixtures" in body or "TB3_" in body or "/opt/" in body):
        return True
    opt = Path("/opt/verifier-fixtures")
    return opt.is_dir()


def _has_reference_impl(task_dir: Path) -> bool:
    body = _combined_test_body(task_dir)
    return bool(body) and ("reference_" in body or "def reference" in body.lower())


def _has_staging_test(task_dir: Path) -> bool:
    body = _combined_test_body(task_dir).lower()
    return bool(body) and ("snapshot" in body or "staging" in body)


def _has_decoy_module(task_dir: Path) -> bool:
    env = task_dir / "environment"
    if not env.is_dir():
        return False
    decoy_names = ("wrap.go", "merge/apply.go", "apply.go", "wrap.rs", "decoy", "_legacy")
    for p in env.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(env)).replace("\\", "/").lower()
        for n in decoy_names:
            if n in rel:
                return True
    # Rust/Go ingest→staging→export split: export stage separate from bind/staging
    rust_src = env / "src"
    if rust_src.is_dir():
        names = {p.name.lower() for p in rust_src.rglob("*.rs")}
        if "emit_stage.rs" in names and ("staging.rs" in names or "compose_bind.rs" in names):
            return True
    go_src = env / "internal"
    if go_src.is_dir():
        paths = [str(p).lower() for p in go_src.rglob("*.go")]
        if any("export_stage" in p for p in paths) and any(
            x in p for p in paths for x in ("staging", "ingest", "wrap", "merge")
        ):
            return True
    cpp_src = env / "src"
    if cpp_src.is_dir():
        names = {p.name.lower() for p in cpp_src.rglob("*.cpp")} | {
            p.name.lower() for p in cpp_src.rglob("*.cc")
        }
        if any("export" in n for n in names) and any(
            x in n for n in names for x in ("staging", "ingest", "merge", "bind", "decoy", "wrap")
        ):
            return True
    return False


def _test_count(task_dir: Path) -> int:
    body = _combined_test_body(task_dir)
    return len(re.findall(r"^\s*def test_", body, re.M))


def _hidden_trap_test_count(task_dir: Path) -> int:
    body = _combined_test_body(task_dir)
    if not body:
        return 0
    count = 0
    for chunk in re.split(r"(?=^\s*def test_)", body, flags=re.M):
        if not chunk.strip().startswith("def test_"):
            continue
        if re.search(r"verifier-fixtures|TB3_[A-Z0-9_]+|/opt/verifier", chunk, re.I):
            count += 1
    return count


def run_probes(task_dir: Path) -> dict[str, dict[str, str]]:
    probes: dict[str, dict[str, str]] = {}
    doc_n = _count_docs_in_instruction(task_dir)
    modules = _env_module_count(task_dir)
    env_files = _env_source_file_count(task_dir)
    tests_n = _test_count(task_dir)
    hidden = _has_hidden_fixtures(task_dir)
    reference = _has_reference_impl(task_dir)
    cli_export = _is_compile_cli_export(task_dir)
    persistence = _needs_persistence_probe(task_dir)

    min_tests = _min_tests(task_dir)
    sol_files = _count_solution_files(task_dir)
    subprocess_ok = _tests_use_subprocess(task_dir)
    rebuild_ok = _test_sh_rebuilds(task_dir)

    min_sol = 5 if _task_difficulty(task_dir) == "hard" else 3
    hidden_test_count = _hidden_trap_test_count(task_dir)

    # Probe 1 — structural depth (first-upload TRIVIAL lock — stricter bar)
    depth_ok = modules >= 5
    p1_ok = (
        depth_ok
        and tests_n >= min_tests
        and reference
        and subprocess_ok
        and sol_files >= min_sol
        and hidden_test_count >= 2
    )
    probes["1_single_file"] = {
        "status": "PASS" if p1_ok else "FAIL",
        "evidence": (
            f"dirs={modules} env_files={env_files} tests={tests_n} ref={reference} "
            f"subprocess={subprocess_ok} solution_files={sol_files} "
            f"hidden_trap_tests={hidden_test_count}"
        ),
    }

    # Probe 3 — hidden vs bundled split
    p3_ok = hidden and reference
    probes["3_hidden_vs_bundled"] = {
        "status": "PASS" if p3_ok else "FAIL",
        "evidence": f"hidden_refs={hidden} reference={reference}",
    }

    # Probe 4 — almost-correct trap (hidden + enough tests)
    p4_ok = hidden and tests_n >= min_tests
    probes["4_almost_correct_trap"] = {
        "status": "PASS" if p4_ok else "FAIL",
        "evidence": f"hidden={hidden} tests={tests_n} (need ≥{min_tests})",
    }

    # Probe 5 — doc depth
    probes["5_doc_depth"] = {
        "status": "PASS" if doc_n >= 3 else "FAIL",
        "evidence": f"instruction cites {doc_n} /app/docs/*.md",
    }

    if persistence:
        body = _combined_test_body(task_dir).lower()
        p2_ok = any(k in body for k in ("cross", "replay", "idempoten", "sequence", "persist"))
        probes["2_persistence_omitted"] = {
            "status": "PASS" if p2_ok else "FAIL",
            "evidence": "persistence/replay tests present" if p2_ok else "missing persistence tests",
        }

    if cli_export:
        staging = _has_staging_test(task_dir)
        decoy = _has_decoy_module(task_dir)
        env_body = ""
        env = task_dir / "environment"
        if env.is_dir():
            env_body = "\n".join(
                p.read_text(encoding="utf-8", errors="replace")
                for p in list(env.rglob("*.go"))[:40]
                + list(env.rglob("*.rs"))[:40]
            ).lower()
        has_ingest = "ingest" in env_body or "ingest" in _combined_test_body(task_dir).lower()
        has_export = "export" in env_body or "export" in _combined_test_body(task_dir).lower()
        probes["1b_decoy_only"] = {
            "status": "PASS" if decoy else "FAIL",
            "evidence": f"decoy_module={decoy}",
        }
        probes["7_staging_artifact"] = {
            "status": "PASS" if staging else "FAIL",
            "evidence": f"staging_snapshot_test={staging}",
        }
        probes["8_ingest_only_patch"] = {
            "status": "PASS" if staging and has_ingest and has_export and rebuild_ok else "FAIL",
            "evidence": (
                f"ingest={has_ingest} export={has_export} staging_test={staging} "
                f"rebuild_in_test_sh={rebuild_ok} dirs={modules}"
            ),
        }

    required = _required_probe_keys(task_dir)
    for key in required:
        probes.setdefault(key, {"status": "FAIL", "evidence": "not evaluated"})

    return probes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "record-args"), default="json")
    args = parser.parse_args()

    task_dir = args.task_dir.resolve()
    if not task_dir.is_dir():
        print(f"ERROR: task dir not found: {task_dir}", file=sys.stderr)
        return 1

    slug = task_dir.name
    probes = run_probes(task_dir)
    any_fail = any(p.get("status") == "FAIL" for p in probes.values())
    payload = {
        "slug": slug,
        "verdict": "PASS" if not any_fail else "FAIL",
        "probes": probes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    out = jobs_path(f"auto-probes-{slug}.json", mkdir=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.format == "record-args":
        short_keys = {
            "1_single_file": "1",
            "1b_decoy_only": "1b",
            "2_persistence_omitted": "2",
            "3_hidden_vs_bundled": "3",
            "4_almost_correct_trap": "4",
            "5_doc_depth": "5",
            "7_staging_artifact": "7",
            "8_ingest_only_patch": "8",
        }
        parts: list[str] = []
        for key in sorted(probes.keys()):
            entry = probes[key]
            short = short_keys.get(key, key)
            ev = entry.get("evidence", "").replace(" ", "_")
            parts.append(f"--probe {short}={entry['status']}:{ev}")
        print(" ".join(parts))
        return 0 if not any_fail else 1

    print(json.dumps(payload, indent=2))
    print(f"\nReport: {out.relative_to(REPO_ROOT)}")
    return 0 if not any_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
