#!/usr/bin/env python3
"""Shared policy: no debugging / no software-engineering tasks (task-generation-mandatory.mdc)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

RULE = "shared/task-generation-mandatory.mdc"
REPOSITORY_STATE_RULE = "shared/repository-state-requirement.mdc"
FAIL_FIX_RULE = "shared/repository-state-fail-fix.mdc"
FORBIDDEN_REPAIR_RULE = "shared/forbidden-repair-objectives-gate.mdc"

REGENERATE_CHECKS = frozenset({"H1", "H3", "H5", "H7"})

BLOCKED_CATEGORIES = frozenset(
    {
        "debugging",
        "software-engineering",
        "data-processing",
        "security",
        "cloud-devops",
        "system-administration",
        "system-configuration-and-setup",
        "build-and-dependency-management",
        "scientific-computing",
    }
)

# Accepted categories (H6) — allowlist only (task-toml-category-gate.mdc).
# LOCKED 2026-07-27: platform accepts only Data Administration / ML / Game.
# category_classifier must also predict these labels (not SE).
ACCEPTED_CATEGORIES = frozenset(
    {
        "data-administration",
        "machine-learning",
        "games",
    }
)

REPAIR_SLUG_TOKENS = frozenset(
    {
        "repair",
        "debug",
        "bugfix",
        "broken",
        "restore",
        "patch",
        "fix",
        "fixing",
        "seeded-bug",
        "triage",
    }
)

SOFTWARE_SLUG_TOKENS = frozenset(
    {
        "repair",
        "fix",
        "triage",
        "reconciler",
        "rollback",
        "hotfix",
    }
)

OBJECTIVE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # (pattern, label, check_id)
    (re.compile(r"\bfix(?:ing)?\s+(?:the|a|an|this|that)\s+broken\b", re.I), "fixing broken …", "H1"),
    (re.compile(r"\bfix(?:ing)?\s+(?:the|a|an)\s+\w+", re.I), "fix the … (repair objective)", "H1"),
    (re.compile(r"\brepair(?:ing)?\s+(?:the|a|an|broken)\b", re.I), "repair …", "H1"),
    (re.compile(r"\bpatch(?:ing)?\s+(?:the|a|an|broken)\b", re.I), "patch …", "H1"),
    (re.compile(r"\bdebug(?:ging)?\s+(?:the|a|an|this)\b", re.I), "debug …", "H1"),
    (re.compile(r"\bbroken\s+(?:service|module|implementation|parser|validator|engine|repository|codebase)\b", re.I), "broken …", "H1"),
    (re.compile(r"\bincomplete\s+implementation\b", re.I), "incomplete implementation", "H1"),
    (re.compile(r"\bunfinished\s+implementation\b", re.I), "unfinished implementation", "H1"),
    (re.compile(r"\brestore\s+(?:missing\s+)?functionality\b", re.I), "restore functionality", "H7"),
    (re.compile(r"\bcorrect(?:ing)?\s+existing\b", re.I), "correcting existing …", "H3"),
    (re.compile(r"\bresolve\s+(?:the\s+)?bug\b", re.I), "resolve bug", "H1"),
    (re.compile(r"\bresolve\s+failure\b", re.I), "resolve failure", "H1"),
    (re.compile(r"\bmake\s+(?:the\s+)?tests\s+pass\b", re.I), "make tests pass", "H5"),
    (re.compile(r"\bfailing\s+implementation\b", re.I), "failing implementation", "H1"),
    (re.compile(r"\bseeded\s+bug", re.I), "seeded bug", "H2"),
    (re.compile(r"\bintentionally\s+broken\b", re.I), "intentionally broken", "H2"),
    (re.compile(r"\bidentify\s+what\s+is\s+wrong\b", re.I), "identify what is wrong", "H5"),
    (re.compile(r"\bfind\s+(?:and\s+)?fix\b", re.I), "find and fix", "H5"),
    (re.compile(r"\bwhat\s+is\s+wrong\s+and\s+fix\b", re.I), "what is wrong and fix", "H5"),
    (re.compile(r"\binvestigat(?:e|ing)\s+seeded\s+bug", re.I), "investigating seeded bugs", "H1"),
    (re.compile(r"\bafter\s+repair\b", re.I), "after repair workflow", "H7"),
    (re.compile(r"\brepair\s+the\s+\w+", re.I), "repair the …", "H1"),
    (re.compile(r"\bno\s+longer\s+produce\s+a\s+correct\b", re.I), "broken output repair shape", "H3"),
    (re.compile(r"\bcorrecting\s+existing\s+behavior\b", re.I), "correcting existing behavior", "H3"),
    (re.compile(r"\bfixing\s+bugs\b", re.I), "fixing bugs", "H1"),
    (re.compile(r"\brepairing\s+broken\b", re.I), "repairing broken", "H1"),
    (re.compile(r"\bresolving\s+failing\s+tests\b", re.I), "resolving failing tests", "H5"),
    (re.compile(r"\bupdating\s+code\s+solely\s+to\s+satisfy\b", re.I), "update code to satisfy tests", "H3"),
    (re.compile(r"\bcorrection\s+workflow\b", re.I), "correction workflow", "H7"),
    (re.compile(r"\brestoration\s+workflow\b", re.I), "restoration workflow", "H7"),
    (re.compile(r"\bcomplet(?:e|ing)\s+(?:an\s+)?intentionally\s+incomplete\b", re.I), "complete intentionally incomplete implementation", "H1"),
    (re.compile(r"\bmaking\s+(?:a\s+)?broken\s+repository\s+work\b", re.I), "making broken repository work", "H2"),
    (re.compile(r"\bfinding\s+defects\s+in\s+existing\s+code\b", re.I), "finding defects in existing code", "H5"),
    (re.compile(r"\brepairing\s+(?:parsers?|validators?|schedulers?|engines?|services?)\b", re.I), "repairing parser/validator/scheduler/engine/service", "H1"),
    (re.compile(r"\bpatching\s+source\s+code\b", re.I), "patching source code", "H7"),
    (re.compile(r"\brepair\s+implementation\b", re.I), "repair implementation", "H7"),
    (re.compile(r"\bbroken\s+module\b", re.I), "broken module", "H1"),
    (re.compile(r"\brestoring\s+missing\s+functionality\b", re.I), "restoring missing functionality", "H7"),
    (re.compile(r"\bresolving\s+failing\s+tests\b", re.I), "resolving failing tests", "H5"),
    (re.compile(r"\binvestigating\s+seeded\s+bugs\b", re.I), "investigating seeded bugs", "H1"),
]

# Forbidden terminology as **core objective** — instruction/idea opening (first paragraph).
FORBIDDEN_OPENING_PHRASES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bresolve\s+bug\b", re.I), "resolve bug", "H1"),
    (re.compile(r"\bresolve\s+failure\b", re.I), "resolve failure", "H1"),
    (re.compile(r"\bmake\s+(?:the\s+)?tests\s+pass\b", re.I), "make tests pass", "H5"),
    (re.compile(r"\bfailing\s+implementation\b", re.I), "failing implementation", "H1"),
    (re.compile(r"\brepair\s+implementation\b", re.I), "repair implementation", "H7"),
    (re.compile(r"\bbroken\s+module\b", re.I), "broken module", "H1"),
    (re.compile(r"\bunfinished\s+implementation\b", re.I), "unfinished implementation", "H1"),
    (re.compile(r"\bincomplete\s+implementation\b", re.I), "incomplete implementation", "H1"),
    (re.compile(r"\bfixing\s+bugs\b", re.I), "fixing bugs", "H1"),
    (re.compile(r"\brepairing\s+broken\b", re.I), "repairing broken", "H1"),
    (re.compile(r"\bpatching\s+source\b", re.I), "patching source", "H7"),
    (re.compile(r"\brestor(?:e|ing)\s+missing\b", re.I), "restore missing", "H7"),
    (re.compile(r"\bcorrect(?:ing)?\s+existing\b", re.I), "correct existing", "H3"),
    (re.compile(r"\bseeded\s+bug", re.I), "seeded bug", "H2"),
    (re.compile(r"\bbroken\s+repository\b", re.I), "broken repository", "H2"),
    (re.compile(r"\bintentionally\s+incomplete\b", re.I), "intentionally incomplete", "H1"),
    (re.compile(r"\bfind(?:ing)?\s+(?:and\s+)?fix\b", re.I), "find and fix", "H5"),
    (re.compile(r"\bidentify\s+what\s+is\s+wrong\b", re.I), "identify what is wrong", "H5"),
]

# Single-word core terms in opening head (first ~350 chars) — repair/debug lane.
FORBIDDEN_OPENING_HEAD_TERMS: list[tuple[str, str]] = [
    ("repair", "H7"),
    ("debug", "H1"),
    ("broken", "H1"),
    ("restore", "H7"),
    ("patch", "H7"),
    ("incomplete", "H1"),
    ("unfinished", "H1"),
]

SOFTWARE_OBJECTIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bsoftware[- ]engineering\b", re.I), "software-engineering objective"),
    (re.compile(r"\bservice\s+under\s+/app\s+is\s+producing\b", re.I), "classic repair service prompt"),
    (re.compile(r"\b(?:import|export|ingest)\s+service\s+under\s+/app\b", re.I), "fix-the-service shape"),
    (re.compile(r"\bis\s+producing\s+(?:wrong|incorrect|inconsistent)\b", re.I), "fix wrong output shape"),
    (re.compile(r"\bfix\s+the\s+service\b", re.I), "fix the service"),
    (re.compile(r"\brepair\s+the\s+(?:service|application|api|app)\b", re.I), "repair the service/API"),
    (re.compile(r"\bbroken\s+service\b", re.I), "broken service"),
    (re.compile(r"\bmake\s+the\s+(?:service|api|application)\s+work\b", re.I), "make service work"),
    (re.compile(r"\bexisting\s+functionality\b", re.I), "fix existing functionality"),
    (re.compile(r"\brestore\s+missing\s+functionality\b", re.I), "restore missing functionality"),
]

BUILD_FRAMING = re.compile(
    r"\b("
    r"implement|build|construct|create|generate|analyze|analyse|model|"
    r"compute|design|develop|produce|establish|derive|assess|evaluate|"
    r"coordinate|export\s+new|add\s+a\s+new|add\s+new\s+capabilit|"
    r"new\s+subsystem|new\s+workflow|analytical\s+outputs?|"
    r"scientific\s+computation|security\s+analysis|reproducibility|"
    r"dependency[- ]management|governance|compliance\s+reasoning|"
    r"reports?\s+from\s+complex|planner|ingest|staging|publish|"
    r"closure|traverse|weave|rollup|correlat"
    r")\b",
    re.I,
)

# Explicit allowed agent goals (repository-state-requirement.mdc)
ALLOWED_AGENT_GOAL = re.compile(
    r"\b("
    r"add\s+(?:a\s+)?new\s+capabilit\w*|"
    r"build\s+(?:a\s+)?new\s+subsystem|"
    r"construct\s+(?:a\s+)?planner|"
    r"implement\s+(?:a\s+)?new\s+workflow|"
    r"generate\s+analytical\s+outputs?|"
    r"scientific\s+computation|"
    r"security\s+analysis\s+engine|"
    r"reproducibility\s+artifacts?|"
    r"build[- ]dependency[- ]management\s+functionality|"
    r"dependency[- ]management\s+functionality|"
    r"governance\s+(?:or\s+)?compliance\s+reasoning|"
    r"compliance\s+reasoning|"
    r"generate\s+reports?\s+from\s+complex\s+datasets|"
    r"provenance|lineage|topology\s+analysis"
    r")\b",
    re.I,
)

FORBIDDEN_REPO_STATE = [
    (
        re.compile(
            r"\bidentify\s+what\s+is\s+wrong\s+and\s+fix\b",
            re.I,
        ),
        "identify what is wrong and fix it",
        "H5",
    ),
    (
        re.compile(
            r"\bthe\s+(?:repository|codebase|project|service|application)\s+"
            r"(?:is|was|remains)\s+broken\b",
            re.I,
        ),
        "repository/service framed as broken",
        "H2",
    ),
    (
        re.compile(r"\bintentionally\s+(?:left\s+)?(?:broken|defective)\b", re.I),
        "intentionally broken repository",
        "H2",
    ),
    (
        re.compile(r"\bseeded\s+(?:with\s+)?bugs?\b", re.I),
        "seeded bugs in repository",
        "H2",
    ),
    (
        re.compile(
            r"\b(?:does\s+not|won't|will\s+not)\s+(?:compile|build)\b",
            re.I,
        ),
        "non-buildable baseline as agent fix target",
        "H2",
    ),
]

FORBIDDEN_TAG_TOKENS = frozenset(
    {
        "debugging",
        "debug",
        "repair",
        "bug-fix",
        "bugfix",
        "fix-bug",
        "broken-code",
        "software-engineering",
        "api-repair",
        "service-repair",
    }
)

HARD_CHECK_LABELS = {
    "H1": "task is NOT debugging",
    "H2": "repository is functional, buildable, consistent — NOT intentionally broken",
    "H3": "agent is NOT fixing existing functionality",
    "H4": "agent adds capability / subsystem / workflow / analysis (NEW — not find-and-fix)",
    "H5": 'not summarizable as "find the bug and make tests pass"',
    "H6": "accepted category (data-administration / machine-learning / games only)",
    "H7": "not a repair, patch, correction, or restoration workflow",
}


@dataclass
class HardAcceptanceAudit:
    violations: list[str] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)  # H1: PASS | FAIL: reason
    regenerate_required: bool = False
    regenerate_reasons: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(v == "PASS" for v in self.checks.values()) and not self.violations

    def finalize_checks(self) -> None:
        for key in HARD_CHECK_LABELS:
            self.checks.setdefault(key, "PASS")

    def mark_regenerate(self, reason: str) -> None:
        self.regenerate_required = True
        if reason not in self.regenerate_reasons:
            self.regenerate_reasons.append(reason)


def _opening_paragraph(text: str, *, limit: int = 900) -> str:
    text = text.strip()
    if not text:
        return ""
    parts = re.split(r"\n\s*\n", text)
    opening = parts[0] if parts else text
    return opening[:limit]


def _scan_forbidden_opening(opening: str, *, source: str) -> list[tuple[str, str]]:
    """Forbidden terminology as core objective in opening paragraph."""
    hits: list[tuple[str, str]] = []
    if not opening.strip():
        return hits
    head = opening[:350]
    for pat, label, check_id in FORBIDDEN_OPENING_PHRASES:
        m = pat.search(opening)
        if not m:
            continue
        snippet = opening[m.start() : m.end()].strip()
        hits.append((check_id, f"{source}: forbidden core term «{label}» — «{snippet}»"))
    for term, check_id in FORBIDDEN_OPENING_HEAD_TERMS:
        if not re.search(rf"\b{re.escape(term)}\b", head, re.I):
            continue
        if term == "patch" and re.search(r"\bprefix\b", head, re.I):
            continue
        hits.append((check_id, f"{source}: forbidden core term «{term}» in opening"))
    if re.search(r"(?<![a-z])fix(?:ing)?(?![a-z])", head, re.I):
        if not re.search(r"\bprefix\b", head, re.I):
            hits.append(("H1", f"{source}: forbidden core term «fix/fixing» in opening"))
    if re.search(r"\bcorrect(?:ing|ion)?\b", head, re.I):
        if not re.search(r"\bcorrectness\b", head, re.I):
            hits.append(("H3", f"{source}: forbidden core term «correct» in opening"))
    return hits


def _apply_regenerate_from_failures(
    audit: HardAcceptanceAudit, check_failures: dict[str, list[str]]
) -> None:
    for check_id in REGENERATE_CHECKS:
        for msg in check_failures.get(check_id, []):
            audit.mark_regenerate(msg)


def _slug_tokens(slug: str, pool: frozenset[str]) -> list[str]:
    parts = {p.lower() for p in slug.split("-") if p}
    return sorted(parts & pool)


def _scan_objectives(text: str, *, source: str) -> list[tuple[str, str]]:
    """Return list of (check_id, message)."""
    hits: list[tuple[str, str]] = []
    if not text or not text.strip():
        return hits
    lower = text.lower()
    if re.search(r"\bfind\s+the\s+bug\b", lower):
        hits.append(("H5", f"{source}: find the bug"))
    if "make the tests pass" in lower or "make tests pass" in lower:
        hits.append(("H5", f"{source}: make tests pass"))

    for pat, label, check_id in OBJECTIVE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        start = max(0, m.start() - 120)
        end = min(len(text), m.end() + 120)
        window = text[start:end]
        if BUILD_FRAMING.search(window) and not re.search(
            r"\b(broken|repair|patch|debug|fixing\s+bug|producing\s+wrong)\b", window, re.I
        ):
            continue
        snippet = text[m.start() : m.end()].strip()
        hits.append((check_id, f"{source}: {label} — «{snippet}»"))

    for pat, label in SOFTWARE_OBJECTIVE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        snippet = text[m.start() : m.end()].strip()
        hits.append(("H1", f"{source}: software-engineering shape — {label} — «{snippet}»"))
        hits.append(("H3", f"{source}: software-engineering shape — {label} — «{snippet}»"))
    return hits


def _scan_repository_state(text: str, *, source: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for pat, label, check_id in FORBIDDEN_REPO_STATE:
        m = pat.search(text)
        if not m:
            continue
        snippet = text[m.start() : m.end()].strip()
        hits.append((check_id, f"{source}: {label} — «{snippet}»"))
    return hits


def _has_new_capability_framing(text: str) -> bool:
    if not text.strip():
        return False
    return bool(BUILD_FRAMING.search(text) or ALLOWED_AGENT_GOAL.search(text))


def _compiled_stack_paths(task_dir: Path) -> list[Path]:
    env = task_dir / "environment"
    markers = (
        env / "go.mod",
        env / "Cargo.toml",
        env / "package.json",
        env / "Makefile",
    )
    return [p for p in markers if p.is_file()]


def _audit_buildable_baseline(task_dir: Path, check_failures: dict[str, list[str]]) -> None:
    """Pack-time: compiled stacks should rebuild before pytest (functional baseline).

    Rebuild may live in tests/test.sh or pytest fixtures (conftest.py / test_outputs.py)
    so test.sh can stay reward-only per reviewer guidance.
    """
    compiled = _compiled_stack_paths(task_dir)
    if not compiled:
        return
    tests = task_dir / "tests"
    if not tests.is_dir():
        msg = "tests/ missing — cannot verify buildable baseline (H2)"
        check_failures["H2"].append(msg)
        return
    rebuild_signals = (
        "cargo build",
        "go build",
        "npm run build",
        "rebuild-",
        "make ",
    )
    candidates = [
        tests / "test.sh",
        tests / "conftest.py",
        tests / "test_outputs.py",
        *sorted(tests.glob("verifier-rebuild*")),
    ]
    bodies: list[str] = []
    for path in candidates:
        if path.is_file():
            bodies.append(path.read_text(encoding="utf-8", errors="replace").lower())
    if not bodies:
        msg = "tests/test.sh missing — cannot verify buildable baseline (H2)"
        check_failures["H2"].append(msg)
        return
    combined = "\n".join(bodies)
    if not any(sig in combined for sig in rebuild_signals):
        msg = (
            "tests/: no rebuild before pytest (test.sh or fixtures) — "
            "baseline may not be buildable (H2)"
        )
        check_failures["H2"].append(msg)


def collect_instruction_paths(task_dir: Path) -> list[Path]:
    if (task_dir / "steps").is_dir():
        return sorted((task_dir / "steps").glob("milestone_*/instruction.md"))
    inst = task_dir / "instruction.md"
    return [inst] if inst.is_file() else []


def read_category_and_tags(task_dir: Path) -> tuple[str, list[str]]:
    toml = task_dir / "task.toml"
    if not toml.is_file():
        return "", []
    body = toml.read_text(encoding="utf-8", errors="replace")
    cat_m = re.search(r'^category\s*=\s*"([^"]+)"', body, re.MULTILINE)
    category = (cat_m.group(1) if cat_m else "").strip().lower()
    tags_m = re.search(r"tags\s*=\s*\[(.*?)\]", body, re.DOTALL)
    tags: list[str] = []
    if tags_m:
        tags = re.findall(r'"([^"]+)"', tags_m.group(1))
    return category, [t.lower() for t in tags]


def audit_task_dir(task_dir: Path) -> HardAcceptanceAudit:
    """Run all 7 hard acceptance checks — any FAIL blocks zip."""
    slug = task_dir.name
    audit = HardAcceptanceAudit()
    check_failures: dict[str, list[str]] = {k: [] for k in HARD_CHECK_LABELS}

    for tok in _slug_tokens(slug, REPAIR_SLUG_TOKENS):
        msg = f"slug: repair/debug token «{tok}» in {slug}"
        audit.violations.append(msg)
        check_failures["H1"].append(msg)
        check_failures["H7"].append(msg)
        audit.mark_regenerate(msg)

    if slug.startswith("repair-") or slug.startswith("fix-") or slug.startswith("debug-"):
        msg = f"slug: repair/software lane prefix in {slug}"
        audit.violations.append(msg)
        check_failures["H1"].append(msg)
        check_failures["H7"].append(msg)
        audit.mark_regenerate(msg)

    category, tags = read_category_and_tags(task_dir)
    if not category:
        msg = "task.toml: missing category"
        audit.violations.append(msg)
        check_failures["H6"].append(msg)
    elif category in BLOCKED_CATEGORIES:
        msg = (
            f'task.toml: category="{category}" — use data-administration, '
            "machine-learning, or games only"
        )
        audit.violations.append(msg)
        check_failures["H1"].append(msg)
        check_failures["H6"].append(msg)
    elif category not in ACCEPTED_CATEGORIES:
        msg = (
            f'task.toml: category="{category}" — use one of: '
            f"{', '.join(sorted(ACCEPTED_CATEGORIES))}"
        )
        audit.violations.append(msg)
        check_failures["H6"].append(msg)

    for tag in tags:
        if tag in FORBIDDEN_TAG_TOKENS or any(
            x in tag for x in ("bug-fix", "debug", "repair", "software-engineering")
        ):
            msg = f'task.toml: tag "{tag}" signals debugging/software-engineering lane'
            audit.violations.append(msg)
            check_failures["H1"].append(msg)
            check_failures["H6"].append(msg)

    instruction_blob = ""
    for inst_path in collect_instruction_paths(task_dir):
        rel = inst_path.relative_to(task_dir)
        text = inst_path.read_text(encoding="utf-8", errors="replace")
        instruction_blob += text + "\n"
        for check_id, msg in _scan_objectives(text, source=str(rel)):
            audit.violations.append(msg)
            check_failures[check_id].append(msg)
        for check_id, msg in _scan_repository_state(text, source=str(rel)):
            audit.violations.append(msg)
            check_failures[check_id].append(msg)
        opening = _opening_paragraph(text)
        for check_id, msg in _scan_forbidden_opening(opening, source=f"{rel} opening"):
            audit.violations.append(msg)
            check_failures[check_id].append(msg)

    if instruction_blob.strip():
        if not _has_new_capability_framing(instruction_blob):
            msg = (
                "instruction: no new-capability framing — add/build subsystem/workflow/"
                "analysis goal (H4); see repository-state-requirement.mdc"
            )
            audit.violations.append(msg)
            check_failures["H4"].append(msg)
    else:
        msg = "missing instruction.md"
        audit.violations.append(msg)
        check_failures["H4"].append(msg)

    solve_paths: list[Path] = []
    if (task_dir / "solution" / "solve.sh").is_file():
        solve_paths.append(task_dir / "solution" / "solve.sh")
    solve_paths.extend(sorted((task_dir / "steps").glob("milestone_*/solution/solve*.sh")))
    for solve in solve_paths:
        body = solve.read_text(encoding="utf-8", errors="replace").lower()
        rel = solve.relative_to(task_dir)
        if re.search(r"\b(cp|patch|apply)\b", body) and not re.search(
            r"\b(cargo build|go build|npm run build|mix compile|cmake|make\b)\b", body
        ):
            if any(
                p in body
                for p in ("solution/files", "solution/patches", "/patches/", "fixed/")
            ):
                msg = f"{rel}: patch/copy-only oracle — repair workflow (H3/H7)"
                audit.violations.append(msg)
                check_failures["H3"].append(msg)
                check_failures["H7"].append(msg)

    env = task_dir / "environment"
    env_skip_parts = frozenset(
        {"vendor", "node_modules", ".git", "__pycache__", "target", "dist", "build"}
    )
    if env.is_dir():
        for path in env.rglob("*"):
            if not path.is_file() or path.suffix in (".png", ".jpg", ".gif", ".zip"):
                continue
            if any(part in env_skip_parts for part in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"\bINTENTIONALLY\s+BROKEN\b", text, re.I):
                msg = f"environment: intentionally broken — {path.relative_to(task_dir)} (H2)"
                audit.violations.append(msg)
                check_failures["H2"].append(msg)
            if re.search(r"\bBUG\s*:", text, re.I):
                msg = f"environment: seeded BUG — {path.relative_to(task_dir)} (H2)"
                audit.violations.append(msg)
                check_failures["H2"].append(msg)

    _audit_buildable_baseline(task_dir, check_failures)

    _apply_regenerate_from_failures(audit, check_failures)

    for check_id, label in HARD_CHECK_LABELS.items():
        fails = check_failures[check_id]
        if fails:
            audit.checks[check_id] = f"FAIL: {fails[0]}"
        else:
            audit.checks[check_id] = "PASS"

    audit.finalize_checks()
    return audit


def audit_idea_text(*, title: str, domain: str, summary: str, slug: str = "") -> HardAcceptanceAudit:
    """Ideas intake — block debugging/software-engineering ideas before CREATE."""
    blob = "\n".join(x for x in (title, domain, summary, slug) if x.strip())
    audit = HardAcceptanceAudit()
    check_failures: dict[str, list[str]] = {k: [] for k in HARD_CHECK_LABELS}

    if slug:
        for tok in _slug_tokens(slug, REPAIR_SLUG_TOKENS):
            msg = f"slug: repair/debug token «{tok}»"
            audit.violations.append(msg)
            check_failures["H1"].append(msg)
            audit.mark_regenerate(msg)

    opening = _opening_paragraph(blob)
    for check_id, msg in _scan_forbidden_opening(opening, source="idea opening"):
        audit.violations.append(msg)
        check_failures[check_id].append(msg)

    for check_id, msg in _scan_objectives(blob, source="idea"):
        audit.violations.append(msg)
        check_failures[check_id].append(msg)

    for check_id, msg in _scan_repository_state(blob, source="idea"):
        audit.violations.append(msg)
        check_failures[check_id].append(msg)

    if blob.strip() and not _has_new_capability_framing(blob):
        msg = (
            "idea: no new-capability framing — add/build subsystem/workflow/analysis (H4)"
        )
        audit.violations.append(msg)
        check_failures["H4"].append(msg)

    if re.search(r"\bsoftware[- ]engineering\b", blob, re.I):
        msg = "idea: software-engineering objective forbidden (H6)"
        audit.violations.append(msg)
        check_failures["H6"].append(msg)

    _apply_regenerate_from_failures(audit, check_failures)

    for check_id in HARD_CHECK_LABELS:
        fails = check_failures[check_id]
        audit.checks[check_id] = f"FAIL: {fails[0]}" if fails else "PASS"

    audit.finalize_checks()
    return audit
