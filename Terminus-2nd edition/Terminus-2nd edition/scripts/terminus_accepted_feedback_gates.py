#!/usr/bin/env python3
"""Optional advisory checks (A-001 … A-010) — NOT in pack_zip / terminus_ci_check.

Manual only when you want a second opinion on accepted-feedback patterns.
Does not block upload. Use accepted-corpus + existing gates for pack.

  python3 scripts/terminus_accepted_feedback_gates.py --task-dir tasks/<name>

Report: jobs-local/accepted-feedback-gates-last.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JOBS_LOCAL = REPO_ROOT / "jobs-local"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from jobs_local_paths import jobs_path, resolve_jobs_path  # noqa: E402

REPORT_JSON = jobs_path("accepted-feedback-gates-last.json")

# Shared with terminus_ci_check.Check shape
@dataclass
class Gate:
    id: str
    severity: str  # block | warn | info
    passed: bool
    message: str
    fix: str = ""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def is_milestone(task_dir: Path) -> bool:
    return (task_dir / "steps").is_dir()


def task_difficulty(task_dir: Path) -> str:
    text = read_text(task_dir / "task.toml")
    m = re.search(r'^difficulty\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1).lower() if m else "unknown"


def compiled_stack(task_dir: Path) -> str | None:
    env = task_dir / "environment"
    if (env / "go.mod").is_file() or (env / "src" / "go.mod").is_file():
        return "go"
    if (env / "Cargo.toml").is_file():
        return "rust"
    if (env / "package.json").is_file():
        return "node"
    if (env / "Makefile").is_file():
        return "make"
    docker = read_text(env / "Dockerfile").lower()
    if "golang" in docker or " go build" in docker:
        return "go"
    if "rust" in docker or "cargo build" in docker:
        return "rust"
    return None


def test_sh_files(task_dir: Path) -> list[Path]:
    if is_milestone(task_dir):
        return list((task_dir / "steps").glob("milestone_*/tests/test.sh"))
    p = task_dir / "tests" / "test.sh"
    return [p] if p.is_file() else []


def test_py_files(task_dir: Path) -> list[Path]:
    files: list[Path] = []
    tests = task_dir / "tests"
    if tests.is_dir():
        files.extend(tests.glob("test*.py"))
    steps = task_dir / "steps"
    if steps.is_dir():
        files.extend(steps.glob("milestone_*/tests/test*.py"))
    return files


# --- A-001: no runtime verifier bootstrap under tests/ ---


def gate_a001_runtime_verifier(task_dir: Path) -> list[Gate]:
    patterns = [
        (r"bootstrap-verifier", "bootstrap-verifier script"),
        (r"python3?\s+-m\s+venv", "runtime venv creation"),
        (r"\bpip\s+install\b", "pip install"),
        (r"\buvx?\s+", "uv/uvx install"),
        (r"npm\s+install", "npm install"),
    ]
    out: list[Gate] = []
    for sh in task_dir.rglob("tests/**/*.sh"):
        if "solution" in sh.parts:
            continue
        text = read_text(sh)
        for pat, label in patterns:
            if re.search(pat, text, re.I):
                out.append(
                    Gate(
                        "A-001_runtime_verifier",
                        "block",
                        False,
                        f"{sh.relative_to(task_dir)}: {label}",
                        "Install pytest in environment/Dockerfile (/opt/verifier-venv); test.sh only invokes it",
                    )
                )
                return out
    docker = read_text(task_dir / "environment" / "Dockerfile")
    has_pytest = "pytest" in docker and (
        "verifier-venv" in docker or "/opt/verifier" in docker
    )
    out.append(
        Gate(
            "A-001_runtime_verifier",
            "block",
            has_pytest or is_milestone(task_dir),
            "Dockerfile preinstalls verifier pytest"
            if has_pytest
            else "Dockerfile missing /opt/verifier-venv pytest install",
            "Add pytest==9.0.3 + pytest-json-ctrf to Dockerfile (see accepted corpus)",
        )
    )
    return out


# --- A-002: failure marker strings documented ---

FAILURE_STRING_RE = re.compile(
    r"""['"]([^'"]{12,}(?:error|invalid|must|failed|not found|\[at )[^'"]*)['"]""",
    re.I,
)


def gate_a002_failure_markers(task_dir: Path) -> list[Gate]:
    if is_milestone(task_dir):
        return [Gate("A-002_failure_markers", "info", True, "milestone — skipped", "")]

    test_text = "\n".join(read_text(p) for p in test_py_files(task_dir))
    if not test_text:
        return [Gate("A-002_failure_markers", "info", True, "no test py", "")]

    doc_blob = read_text(task_dir / "instruction.md")
    env = task_dir / "environment"
    if env.is_dir():
        for md in env.rglob("*.md"):
            doc_blob += "\n" + read_text(md)

    undocumented: list[str] = []
    for m in FAILURE_STRING_RE.finditer(test_text):
        s = m.group(1).strip()
        if s in doc_blob:
            continue
        # Allow generic pytest / path fragments
        if s.startswith("/app/") and "error" not in s.lower():
            continue
        if len(s) < 20 and "error" not in s.lower():
            continue
        undocumented.append(s[:80])

    if undocumented:
        sample = undocumented[:3]
        return [
            Gate(
                "A-002_failure_markers",
                "block",
                False,
                f"Test asserts stderr/messages not found in instruction or /app/docs: {sample!r}",
                "Add row to failure-markers.md (or staging-contract.md) OR align test to documented string",
            )
        ]
    return [Gate("A-002_failure_markers", "block", True, "failure strings documented or none asserted", "")]


# --- A-003: reference + subprocess ---


def gate_a003_reference_subprocess(task_dir: Path) -> list[Gate]:
    if is_milestone(task_dir):
        return [Gate("A-003_reference_subprocess", "info", True, "milestone — skipped", "")]

    body = "\n".join(read_text(p) for p in test_py_files(task_dir))
    has_ref = "reference_" in body or re.search(r"def\s+reference\w*", body, re.I)
    has_sub = "subprocess" in body
    ok = has_ref and has_sub
    return [
        Gate(
            "A-003_reference_subprocess",
            "block",
            ok,
            "independent reference_* + subprocess"
            if ok
            else f"missing reference={has_ref} subprocess={has_sub}",
            "Add Python reference_* helpers and subprocess CLI runs (accepted ACCEPT pattern)",
        )
    ]


# --- A-004: rebuild in test.sh for compiled stacks ---


def gate_a004_rebuild_test_sh(task_dir: Path) -> list[Gate]:
    stack = compiled_stack(task_dir)
    if not stack:
        return [Gate("A-004_rebuild_test_sh", "info", True, "non-compiled stack — skipped", "")]

    rebuild_tokens = {
        "go": ("go build", "rebuild-"),
        "rust": ("cargo build",),
        "node": ("npm run build", "npm --prefix"),
        "make": ("make", "rebuild-"),
    }
    tokens = rebuild_tokens.get(stack, ("build",))
    tests = task_dir / "tests"
    parts = [read_text(p) for p in test_sh_files(task_dir)]
    for name in ("conftest.py", "test_outputs.py"):
        p = tests / name
        if p.is_file():
            parts.append(read_text(p))
    for p in sorted(tests.glob("verifier-rebuild*")) if tests.is_dir() else []:
        parts.append(read_text(p))
    sh_text = "\n".join(parts)
    ok = any(t in sh_text for t in tokens)
    return [
        Gate(
            "A-004_rebuild_test_sh",
            "block",
            ok,
            f"verifier rebuilds {stack}" if ok else f"compiled {stack} but missing rebuild before pytest",
            f"Add {' / '.join(tokens)} to tests/conftest.py (or test.sh) before pytest",
        )
    ]


# --- A-005: hidden / verifier-only fixtures ---


def gate_a005_hidden_fixtures(task_dir: Path) -> list[Gate]:
    if is_milestone(task_dir):
        return [Gate("A-005_hidden_fixtures", "info", True, "milestone — skipped", "")]

    body = "\n".join(read_text(p) for p in test_py_files(task_dir))
    has_hidden = "/opt/verifier-fixtures" in body or "TB3_" in body
    has_sub = "subprocess" in body
    if not has_sub:
        return [Gate("A-005_hidden_fixtures", "info", True, "no CLI subprocess tests", "")]

    return [
        Gate(
            "A-005_hidden_fixtures",
            "warn",
            has_hidden,
            "hidden fixture or TB3_* env probe present"
            if has_hidden
            else "CLI task lacks /opt/verifier-fixtures or TB3_* anti-cheat",
            "Add ≥1 hidden fixture under /opt/verifier-fixtures (cited in instruction if env override)",
        )
    ]


# --- A-006: schema key-order docs need order tests ---


SCHEMA_ORDER_DOC_RE = re.compile(
    r"(immediately after|fourth field|key order|field order|must be the \w+ field)",
    re.I,
)


def gate_a006_schema_key_order(task_dir: Path) -> list[Gate]:
    env = task_dir / "environment"
    order_docs = False
    for md in env.rglob("*schema*.md") if env.is_dir() else []:
        if SCHEMA_ORDER_DOC_RE.search(read_text(md)):
            order_docs = True
            break
    if not order_docs:
        for md in env.rglob("*.md") if env.is_dir() else []:
            if SCHEMA_ORDER_DOC_RE.search(read_text(md)):
                order_docs = True
                break

    if not order_docs:
        return [Gate("A-006_schema_key_order", "info", True, "no key-order schema docs", "")]

    body = "\n".join(read_text(p) for p in test_py_files(task_dir))
    has_order_test = bool(
        re.search(
            r"key_order|keys\(\)|object_pairs_hook|raw.*json|decode.*object_pairs",
            body,
            re.I,
        )
    )
    return [
        Gate(
            "A-006_schema_key_order",
            "warn",
            has_order_test,
            "key-order schema doc + order-aware test"
            if has_order_test
            else "docs require JSON key order but tests may use json.loads dict only",
            "Assert raw JSON key order (object_pairs_hook) per report-schema.md",
        )
    ]


# --- A-007: difficulty vs recorded agent rates ---


def _worst_rate_from_jobs(slug: str) -> tuple[float | None, str]:
    for name in (f"agent-smoke-{slug}.json", f"trivial-easy-context-{slug}.json"):
        path = JOBS_LOCAL / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if "worst_rate" in data:
            return float(data["worst_rate"]), name
        rates = []
        for key in ("opus", "gpt"):
            entry = data.get(key)
            if isinstance(entry, dict) and "rate" in entry:
                rates.append(float(entry["rate"]))
            elif isinstance(entry, str) and "/" in entry:
                p, n = entry.split("/")
                rates.append(int(p) / int(n))
        if rates:
            return max(rates), name
    return None, ""


def gate_a007_difficulty_sync(task_dir: Path) -> list[Gate]:
    declared = task_difficulty(task_dir)
    worst, src = _worst_rate_from_jobs(task_dir.name)
    if worst is None:
        return [
            Gate(
                "A-007_difficulty_sync",
                "warn",
                True,
                "no agent-smoke record — set difficulty from target; record after platform eval",
                "",
            )
        ]

    # Snorkel bands: hard worst ≤20%, medium >20% and ≤60%, easy >60%
    if worst <= 0.20:
        band = "hard"
    elif worst <= 0.60:
        band = "medium"
    else:
        band = "easy"

    match = (
        (declared == "hard" and band == "hard")
        or (declared == "medium" and band in ("medium", "hard"))
        or (declared == "easy" and band == "easy")
    )
    # Stricter: hard must not be declared when worst > 20%
    if declared == "hard" and worst > 0.20:
        match = False
    if declared == "medium" and worst > 0.60:
        match = False

    return [
        Gate(
            "A-007_difficulty_sync",
            "warn",
            match,
            f"task.toml={declared!r} vs measured worst={worst:.0%} ({band}) from {src}"
            if match
            else f"MISMATCH: task.toml difficulty={declared!r} but {src} worst={worst:.0%} → {band}",
            f"Set difficulty = \"{band}\" in task.toml or harden until worst ≤20% for hard",
        )
    ]


# --- A-008: NOP must fail (reward 0) ---


def gate_a008_nop_discriminates(task_dir: Path) -> list[Gate]:
    path = resolve_jobs_path(f"harbor-verify-{task_dir.name}.json")
    if not path.is_file():
        return [
            Gate(
                "A-008_nop_discriminates",
                "warn",
                True,
                "no harbor-verify cache — run harbor NOP locally",
                "stb harbor run -a nop -p tasks/<name>",
            )
        ]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [Gate("A-008_nop_discriminates", "warn", False, "invalid harbor-verify json", "")]

    nop = str(data.get("nop", "")).strip()
    ok = nop in ("0", "0.0", "0.00")
    failed = data.get("nop_failed_tests")
    extra = f", failed_tests={failed}" if failed is not None else ""
    return [
        Gate(
            "A-008_nop_discriminates",
            "warn",
            ok,
            f"NOP reward={nop}{extra}" if ok else f"NOP reward={nop} (expected 0)",
            "Broken baseline must fail verifier; run harbor nop after oracle",
        )
    ]


# --- A-009: oracle no hardcoded outputs ---


def gate_a009_oracle_no_echo(task_dir: Path) -> list[Gate]:
    out: list[Gate] = []
    echo_pat = re.compile(
        r"(?:echo|printf|cat)\s+.*>\s*(/app/(?:output|state|data)/|/output/)",
        re.I,
    )
    for rel in ("solution/solve.sh",):
        path = task_dir / rel
        if not path.is_file():
            continue
        text = read_text(path)
        if echo_pat.search(text):
            out.append(
                Gate(
                    "A-009_oracle_no_echo",
                    "block",
                    False,
                    f"{rel}: writes final artifact via echo/printf/cat",
                    "Patch /app source and rebuild; no golden file echo",
                )
            )
            return out
        # Also block heredoc to output paths
        if re.search(r">>\s*/app/(?:output|state)/", text):
            out.append(
                Gate(
                    "A-009_oracle_no_echo",
                    "block",
                    False,
                    f"{rel}: heredoc write to output/state",
                    "Use real computation in solve.sh",
                )
            )
            return out
    out.append(Gate("A-009_oracle_no_echo", "block", True, "solve.sh no echo-only outputs", ""))
    return out


# --- A-010: instruction-cited docs exist; test paths trace to contract ---


def gate_a010_instruction_docs(task_dir: Path) -> list[Gate]:
    inst = read_text(task_dir / "instruction.md")
    cited = set(re.findall(r"/app/docs/[a-zA-Z0-9_./-]+\.md", inst))
    missing: list[str] = []
    for doc in cited:
        rel = doc.replace("/app/", "")
        if not (task_dir / "environment" / rel).is_file():
            # also try environment/docs/ basename
            alt = task_dir / "environment" / "docs" / Path(doc).name
            if not alt.is_file():
                missing.append(doc)

    if missing:
        return [
            Gate(
                "A-010_instruction_docs",
                "block",
                False,
                f"instruction cites missing docs: {missing[:5]}",
                "Add doc files under environment/ or fix instruction paths",
            )
        ]

    test_paths = set()
    for tf in test_py_files(task_dir):
        test_paths.update(re.findall(r'["\'](/app/[^"\']+)["\']', read_text(tf)))

    if not cited and test_paths:
        return [
            Gate(
                "A-010_instruction_docs",
                "warn",
                True,
                "instruction does not cite /app/docs — prefer doc pointers for contracts",
                "",
            )
        ]

    return [Gate("A-010_instruction_docs", "block", True, "cited docs exist in environment", "")]


def run_all_gates(task_dir: Path) -> list[Gate]:
    gates: list[Gate] = []
    gates.extend(gate_a001_runtime_verifier(task_dir))
    gates.extend(gate_a002_failure_markers(task_dir))
    gates.extend(gate_a003_reference_subprocess(task_dir))
    gates.extend(gate_a004_rebuild_test_sh(task_dir))
    gates.extend(gate_a005_hidden_fixtures(task_dir))
    gates.extend(gate_a006_schema_key_order(task_dir))
    gates.extend(gate_a007_difficulty_sync(task_dir))
    gates.extend(gate_a008_nop_discriminates(task_dir))
    gates.extend(gate_a009_oracle_no_echo(task_dir))
    gates.extend(gate_a010_instruction_docs(task_dir))
    return gates


def gates_to_checks(gates: list[Gate]) -> list:
    """Convert to terminus_ci_check.Check if imported."""
    try:
        from terminus_ci_check import Check

        return [
            Check(g.id, g.severity, g.passed, g.message, g.fix) for g in gates
        ]
    except ImportError:
        return gates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--pack-gate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task_dir)
    if not task_dir.is_absolute():
        task_dir = REPO_ROOT / task_dir
    task_dir = task_dir.resolve()
    if not (task_dir / "task.toml").is_file():
        print(f"ERROR: not a task dir: {task_dir}", file=sys.stderr)
        return 1

    gates = run_all_gates(task_dir)
    blocks = [g for g in gates if g.severity == "block" and not g.passed]
    warns = [g for g in gates if g.severity == "warn" and not g.passed]
    ok = not blocks

    payload = {
        "slug": task_dir.name,
        "path": str(task_dir),
        "ok": ok,
        "blocking_count": len(blocks),
        "warning_count": len(warns),
        "not_templating_note": (
            "These gates check verifier/oracle/doc hygiene — anti-spam similarity is separate"
        ),
        "gates": [asdict(g) for g in gates],
    }
    JOBS_LOCAL.mkdir(parents=True, exist_ok=True)
    out = jobs_path("accepted-feedback-gates-last.json", mkdir=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"# Accepted-feedback gates — {task_dir.name}")
        print(f"PASS: {sum(1 for g in gates if g.passed)}/{len(gates)} · BLOCK: {len(blocks)} · WARN: {len(warns)}")
        for g in gates:
            mark = "PASS" if g.passed else g.severity.upper()
            print(f"  [{mark}] {g.id}: {g.message[:100]}")
        print(f"\nReport: {REPORT_JSON}")

    if args.pack_gate and blocks:
        print(f"FAIL — {len(blocks)} blocking A-gate(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
