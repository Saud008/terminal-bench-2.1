#!/usr/bin/env python3
"""Delivery gate for a TB 4.0 task — mechanical parts of Master Ship Checklist D/G/H/I.

Covers: delivery structure (98), oracle-nop-evidence structure and test-by-test
status (40, 73-76), duplicated evidence (78, 84), evidence freshness by mtime
(77, 83), test counts vs current tests/ (53), SUMMARY.txt format and rewards
(79, 81), bundle sha recompute (82), per-run file sets (92), xhigh (93),
exception_info (94), path-field PII in config.json/result.json (89),
rubric_score.txt narration and near-duplicates (80, 87), reward-hacking grep
(95), the measured-rate acceptance gate, and the final stb / personal-path /
canary scrub across the whole bundle (89, 90, 99).

Reading trajectories (86, 88, 95 behavior) and every non-mechanical check
remains manual.

Usage:
    py -3 tb40/tb40_ship_check.py <slug-dir>
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

EVIDENCE_RUNS = ("oracle-1", "oracle-2", "oracle-3", "nop-1", "nop-2")
EVIDENCE_FILES = {"ctrf.json", "reward.txt", "test-stdout.txt"}
RUNS = tuple(f"run-0{i}" for i in range(1, 6))
AGENT_REQUIRED = {"api-calls.jsonl", "recording.cast", "trajectory.json"}
VERIFIER_FILES = {"ctrf.json", "reward.txt", "test-stdout.txt"}
INNER_ALLOWED = {"instruction.md", "task.toml", "environment", "solution", "tests"}
OUTER_ALLOWED = {"rubric.txt", "oracle-nop-evidence", "trajectories"}
JUNK_NAMES = {".DS_Store", "__MACOSX", ".git", "__pycache__", "SOURCE.txt", "Thumbs.db", ".pytest_cache", ".ruff_cache"}
AI_SCAFFOLDING = {"claude.md", "agents.md", "skills.md", ".cursor", ".claude", ".cursorrules", ".aider"}
SHA_INPUTS = ("instruction.md", "tests", "environment", "solution", "task.toml")
PII_PATH = re.compile(r"/Users/|/private/tmp/|[A-Za-z]:\\|/mnt/[a-z]/|(?<![A-Za-z0-9_.-])/home/(?!agent\b|app\b|user\b|ubuntu\b|runner\b|node\b)[A-Za-z0-9_.-]+")
GUID = re.compile(rb"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
ID_KEY_BEFORE = re.compile(rb"(?i)[\"']?[\w.-]*(id|uuid|session|trial|job|run|request|call|message|msg|trace|span|key|checksum|digest|hash)[\w.-]*[\"']?\s*[:=]\s*[\"']?(urn:uuid:)?$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []

    def err(self, check: str, msg: str) -> None:
        self.errors.append(f"ERROR [{check}] {msg}")

    def warn(self, check: str, msg: str) -> None:
        self.warns.append(f"WARN  [{check}] {msg}")


def resolve_outer(arg: str) -> Path:
    p = Path(arg).resolve()
    if p.parent.name == p.name and not (p / p.name).is_dir():
        return p.parent
    return p


def is_junk(p: Path) -> bool:
    return p.name in JUNK_NAMES or p.name.startswith("._") or p.suffix == ".pyc"


def load_json(path: Path, r: Report, check: str) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        r.err(check, f"{path}: unreadable JSON ({exc})")
        return None


def ctrf_tests(data: dict) -> tuple[list[dict], dict]:
    results = data.get("results", data)
    return results.get("tests", []), results.get("summary", {})


def read_reward(path: Path) -> float | None:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def bundle_sha(inner: Path) -> str:
    """Emulate: find <SHA_INPUTS> -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -c1-16."""
    paths: list[str] = []
    for name in SHA_INPUTS:
        p = inner / name
        if p.is_file():
            paths.append(name)
        elif p.is_dir():
            paths.extend(q.relative_to(inner).as_posix() for q in p.rglob("*") if q.is_file())
    listing = "".join(
        f"{hashlib.sha256((inner / rel).read_bytes()).hexdigest()}  {rel}\n"
        for rel in sorted(paths, key=lambda s: s.encode())
    )
    return hashlib.sha256(listing.encode()).hexdigest()[:16]


def collected_test_count(tests_dir: Path) -> tuple[int, bool]:
    total, parametrized = 0, False
    for path in tests_dir.rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes: list[ast.AST] = []
        for node in tree.body:
            nodes.extend(node.body if isinstance(node, ast.ClassDef) and node.name.startswith("Test") else [node])
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                total += 1
                if any("parametrize" in ast.unparse(d) for d in node.decorator_list):
                    parametrized = True
    return total, parametrized


def newest_graded_mtime(inner: Path) -> tuple[float, str]:
    best, name = 0.0, ""
    for item in ("instruction.md", "task.toml", "tests", "environment", "solution"):
        p = inner / item
        files = [p] if p.is_file() else ([q for q in p.rglob("*") if q.is_file()] if p.is_dir() else [])
        for f in files:
            m = f.stat().st_mtime
            if m > best:
                best, name = m, f.relative_to(inner).as_posix()
    return best, name


# --------------------------------------------------------------------------- checks


def check_structure(outer: Path, inner: Path, r: Report) -> None:
    slug = outer.name
    if not inner.is_dir():
        r.err("98", f"missing inner task dir {slug}/{slug}/")
        return
    for child in outer.iterdir():
        if child.name != slug and child.name not in OUTER_ALLOWED:
            r.err("98", f"extra item in {slug}/: {child.name}")
    for name in OUTER_ALLOWED:
        if not (outer / name).exists():
            r.err("98", f"missing {slug}/{name}")
    for child in inner.iterdir():
        if child.name not in INNER_ALLOWED:
            r.err("98", f"extra item in {slug}/{slug}/: {child.name}")
    for p in outer.rglob("*"):
        if is_junk(p):
            r.err("98", f"junk must not ship: {p.relative_to(outer).as_posix()}")
        elif p.name.lower() in AI_SCAFFOLDING and p.is_relative_to(inner):
            r.err("98", f"AI-framework scaffolding filename: {p.relative_to(outer).as_posix()}")


def check_evidence(outer: Path, inner: Path, expected_tests: int, parametrized: bool, r: Report) -> list[float]:
    ev = outer / "oracle-nop-evidence"
    stamps: list[float] = []
    if not ev.is_dir():
        return stamps
    present = {p.name for p in ev.iterdir()}
    for extra in sorted(present - set(EVIDENCE_RUNS)):
        r.err("73", f"oracle-nop-evidence has extra item {extra}")
    starts: dict[str, object] = {}
    stdouts: dict[str, bytes] = {}
    for run in EVIDENCE_RUNS:
        d = ev / run
        if not d.is_dir():
            r.err("73", f"missing oracle-nop-evidence/{run}/")
            continue
        names = {p.name for p in d.iterdir()}
        if names != EVIDENCE_FILES:
            r.err("73", f"{run}/ must contain exactly {sorted(EVIDENCE_FILES)} (has {sorted(names)})")
        ctrf_path = d / "ctrf.json"
        if not ctrf_path.is_file():
            continue
        stamps.append(ctrf_path.stat().st_mtime)
        data = load_json(ctrf_path, r, "73")
        if data is None:
            continue
        tests, summary = ctrf_tests(data)
        starts[run] = summary.get("start")
        reward = read_reward(d / "reward.txt")
        count_check(f"oracle-nop-evidence/{run}", len(tests), expected_tests, parametrized, r)
        if run.startswith("oracle"):
            bad = [t.get("name") for t in tests if t.get("status") != "passed"]
            if bad or not tests:
                r.err("74", f"{run}: tests not passing: {bad[:5] or 'no tests recorded'}")
            if reward != 1.0:
                r.err("74", f"{run}: reward.txt is {reward}, expected 1")
        else:
            passed = [t.get("name") for t in tests if t.get("status") == "passed"]
            other = [f"{t.get('name')}={t.get('status')}" for t in tests if t.get("status") not in {"passed", "failed"}]
            if passed:
                r.err("40", f"{run}: tests pass under NOP: {passed[:5]}")
            if other:
                r.err("75", f"{run}: non-'failed' statuses mask results: {other[:5]}")
            if reward != 0.0:
                r.err("75", f"{run}: reward.txt is {reward}, expected 0")
            out = d / "test-stdout.txt"
            if out.is_file():
                text = out.read_text(encoding="utf-8", errors="replace")
                if re.search(r"ModuleNotFoundError|ImportError|SyntaxError|ERROR collecting|errors? during collection|INTERNALERROR|command not found|No such file or directory: '/tests|ERROR at setup of", text):
                    r.err("76", f"{run}: test-stdout shows infrastructure/import/collection/setup errors, not genuine assertion failures")
        if (d / "test-stdout.txt").is_file():
            stdouts[run] = (d / "test-stdout.txt").read_bytes()
    for group in (("oracle-1", "oracle-2", "oracle-3"), ("nop-1", "nop-2")):
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if starts.get(a) is not None and starts.get(a) == starts.get(b):
                    r.err("84", f"{a} and {b} share ctrf start timestamp {starts[a]} — duplicated evidence")
                if a in stdouts and stdouts.get(a) == stdouts.get(b):
                    r.err("78", f"{a} and {b} have byte-identical test-stdout.txt — duplicated evidence")
                addrs_a = set(re.findall(rb"0x[0-9a-f]{8,}", stdouts.get(a, b"")))
                if addrs_a and addrs_a == set(re.findall(rb"0x[0-9a-f]{8,}", stdouts.get(b, b""))):
                    r.warn("84", f"{a} and {b} share identical object addresses — confirm independent runs")
    return stamps


def count_check(where: str, got: int, expected: int, parametrized: bool, r: Report) -> None:
    if parametrized:
        if got < expected:
            r.err("53", f"{where}: ctrf has {got} tests, current tests/ define at least {expected}")
    elif got != expected:
        r.err("53", f"{where}: ctrf has {got} tests, current tests/ collect {expected} — evidence is stale")


def check_trajectories(outer: Path, inner: Path, expected_tests: int, parametrized: bool, r: Report) -> tuple[list[float], list[int]]:
    traj = outer / "trajectories"
    stamps: list[float] = []
    rewards: list[int] = []
    if not traj.is_dir():
        return stamps, rewards
    slug = outer.name
    for child in traj.iterdir():
        if child.name not in set(RUNS) | {"SUMMARY.txt"}:
            r.err("98", f"trajectories/ has extra item {child.name}")

    summary_rewards: list[float] = []
    summary_sha = None
    sp = traj / "SUMMARY.txt"
    if not sp.is_file():
        r.err("79", "trajectories/SUMMARY.txt missing")
    else:
        lines = sp.read_text(encoding="utf-8").rstrip("\n").split("\n")
        if len(lines) != 2:
            r.err("79", f"SUMMARY.txt must be exactly 2 lines (has {len(lines)})")
        first = lines[0] if lines else ""
        if slug not in first:
            r.err("79", "SUMMARY line 1 must contain the slug")
        m = re.search(r"\b[0-9a-f]{16}\b", first)
        summary_sha = m.group(0) if m else None
        if not summary_sha:
            r.err("79", "SUMMARY line 1 must contain the 16-char bundle sha")
        if "gpt-5.6" not in first or "xhigh" not in first:
            r.err("79", "SUMMARY line 1 must contain the model (gpt-5.6) and reasoning_effort (xhigh)")
        if len(lines) > 1:
            summary_rewards = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", lines[1])]
            if len(summary_rewards) != 5:
                r.err("79", f"SUMMARY line 2 must hold 5 rewards (found {len(summary_rewards)})")
        if re.search(r"note:|summary:", sp.read_text(encoding="utf-8"), re.I):
            r.err("79", "SUMMARY.txt contains prose")

    if summary_sha:
        fresh = bundle_sha(inner)
        if fresh != summary_sha:
            r.err("82", f"SUMMARY sha {summary_sha} != fresh recompute {fresh} (byte-order sort; confirm in WSL with LC_ALL=C and the canonical command)")

    agent_sets: dict[str, frozenset[str]] = {}
    scores: dict[str, str] = {}
    for i, run in enumerate(RUNS):
        d = traj / run
        if not d.is_dir():
            r.err("92", f"missing trajectories/{run}/")
            continue
        stamps.append(d.stat().st_mtime)
        agent = d / "agent"
        names = frozenset(p.name for p in agent.iterdir()) if agent.is_dir() else frozenset()
        agent_sets[run] = names
        missing = AGENT_REQUIRED - names
        if missing:
            r.err("92", f"{run}/agent missing {sorted(missing)}")
        if not any(n.endswith(".pane") for n in names):
            r.warn("92", f"{run}/agent has no *.pane file — confirm the equivalent capture exists")

        ver = d / "verifier"
        vnames = {p.name for p in ver.iterdir()} if ver.is_dir() else set()
        if not VERIFIER_FILES <= vnames:
            r.err("92", f"{run}/verifier missing {sorted(VERIFIER_FILES - vnames)}")
        reward = read_reward(ver / "reward.txt")
        if (ver / "ctrf.json").is_file():
            stamps.append((ver / "ctrf.json").stat().st_mtime)
            data = load_json(ver / "ctrf.json", r, "92")
            if data is not None:
                tests, _ = ctrf_tests(data)
                count_check(f"{run}/verifier", len(tests), expected_tests, parametrized, r)
                ctrf_pass = 1.0 if tests and all(t.get("status") == "passed" for t in tests) else 0.0
                if reward is not None and reward != ctrf_pass:
                    r.err("92", f"{run}: reward.txt {reward} disagrees with ctrf outcome {ctrf_pass}")
        if reward is not None:
            rewards.append(int(reward))
            if i < len(summary_rewards) and summary_rewards[i] != reward:
                r.err("81", f"{run}: SUMMARY says {summary_rewards[i]}, reward.txt says {reward}")

        texts = ""
        for name in ("config.json", "result.json"):
            if (d / name).is_file():
                texts += (d / name).read_text(encoding="utf-8", errors="replace")
        efforts = re.findall(r'"reasoning_effort"\s*:\s*"([^"]+)"', texts)
        if not efforts or any(e != "xhigh" for e in efforts):
            r.err("93", f"{run}: reasoning_effort not confirmed xhigh (found {sorted(set(efforts)) or 'none'})")

        for name in ("config.json", "result.json"):
            if not (d / name).is_file():
                r.err("94" if name == "result.json" else "92", f"{run}: {name} missing")
                continue
            obj = load_json(d / name, r, "89")
            if obj is None:
                continue
            check_path_fields(obj, f"{run}/{name}", r)
            if name == "result.json" and find_populated(obj, "exception_info"):
                r.err("94", f"{run}: result.json has exception_info populated — re-run, never ship")

        rs = d / "rubric_score.txt"
        if not rs.is_file():
            r.err("80", f"{run}: rubric_score.txt missing")
        else:
            text = rs.read_text(encoding="utf-8")
            scores[run] = text
            if re.search(r"(?im)^\s*(note|summary)\s*:|strengthened|this session", text):
                r.err("80", f"{run}/rubric_score.txt contains narration/prose")

        tj = agent / "trajectory.json"
        if tj.is_file():
            t = tj.read_text(encoding="utf-8", errors="replace")
            hits = sorted(set(re.findall(r"/tests/|test_outputs\.py|ctrf\.json|reward\.txt|/logs/verifier|/opt/verifier|/solution/|/oracle/", t)))
            if hits:
                r.warn("95", f"{run}: trajectory mentions grading paths {hits} — read and confirm no reads/writes")
            if re.search(r"\[truncated\]|output truncated|\.\.\. \(truncated|<truncated", t, re.I):
                r.err("95", f"{run}: truncation marker in trajectory")

    if len(set(agent_sets.values())) > 1:
        r.err("92", "agent/ file sets differ between runs: " + "; ".join(f"{k}={sorted(v)}" for k, v in agent_sets.items()))

    criteria: list[str] = []
    rubric = outer / "rubric.txt"
    if rubric.is_file():
        criteria = sorted(
            (ln.rsplit(",", 1)[0].strip() for ln in rubric.read_text(encoding="utf-8").splitlines() if ln.strip()),
            key=len,
            reverse=True,
        )

    def own_part(text: str) -> str:
        text = re.sub(r"run-0\d", "", text)
        for c in criteria:
            text = text.replace(c, "")
        return text

    keys = list(scores)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if scores[a] == scores[b]:
                r.err("87", f"{a} and {b} rubric_score.txt are byte-identical — each must cite its own run")
                continue
            ratio = difflib.SequenceMatcher(None, own_part(scores[a]), own_part(scores[b])).ratio()
            if ratio > 0.97:
                r.err("87", f"{a} and {b} rubric_score.txt verdicts/citations are {ratio:.0%} identical — each must cite its own run")
    return stamps, rewards


def find_populated(obj: object, key: str) -> bool:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and v not in (None, "", {}, []):
                return True
            if find_populated(v, key):
                return True
    elif isinstance(obj, list):
        return any(find_populated(v, key) for v in obj)
    return False


def check_path_fields(obj: object, where: str, r: Report, parent: str = "") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                if k in {"path", "trials_dir", "trial_uri", "jobs_dir", "job_dir", "task_dir", "trial_dir"} and PII_PATH.search(v):
                    r.err("89", f"{where} {parent + '.' if parent else ''}{k} = {v!r} leaks a local path — rewrite to /terminal-bench4.0/<slug>")
            else:
                check_path_fields(v, where, r, k)
    elif isinstance(obj, list):
        for v in obj:
            check_path_fields(v, where, r, parent)


def check_gate(rewards: list[int], inner: Path, r: Report) -> None:
    if len(rewards) != 5:
        return
    try:
        meta = tomllib.loads((inner / "task.toml").read_text(encoding="utf-8")).get("metadata", {})
    except (OSError, tomllib.TOMLDecodeError):
        meta = {}
    solved = sum(rewards)
    if solved == 5:
        r.err("gate", "every run solved it — a fully saturated task is never accepted as-is; make it genuinely harder, re-freeze, re-measure")
    elif solved == 4:
        r.warn("gate", "high solve count — no longer an automatic rejection in TB 4.0, but confirm difficulty_explanation holds up and the one failure is a genuine capability failure")
    elif solved == 0:
        r.warn("gate", "no run solved it — classify every failure (capability / spec gap / refusal / infra / reward hack / missing evidence) and confirm none is a spec gap or underivable threshold")
    if solved < 5 and not str(meta.get("difficulty_explanation", "")).strip():
        r.err("gate", "difficulty_explanation is empty — reviewers judge it against these runs")


def scrub(outer: Path, r: Report) -> None:
    patterns = [
        (re.compile(rb"\bstb\b"), "word-boundary 'stb'"),
        (re.compile(rb"/Users/"), "/Users/"),
        (re.compile(rb"/private/tmp/"), "/private/tmp/"),
        (re.compile(rb"[A-Za-z]:\\\\?Users\\\\?"), "Windows user path"),
        (re.compile(rb"reference_pattern"), "reference_pattern"),
        (re.compile(rb"(?i)canary|benchmark data should never"), "canary string"),
    ]
    home = re.compile(rb"(?<![A-Za-z0-9_.-])/home/(?!agent\b|app\b|user\b|ubuntu\b|runner\b|node\b)[A-Za-z0-9_.-]+")
    guid_files: dict[str, int] = {}
    for p in sorted(outer.rglob("*")):
        if not p.is_file():
            continue
        data = p.read_bytes()
        where = p.relative_to(outer).as_posix()
        for rx, label in patterns:
            if rx.search(data):
                r.err("89/99", f"{where}: {label} hit")
        m = home.search(data)
        if m:
            r.err("89/99", f"{where}: {m.group(0).decode(errors='replace')} — only in-container paths like /home/agent are allowed")
        if p.suffix in {".cast", ".jsonl"} and "agent" in p.parts:
            continue
        bare = 0
        for g in GUID.finditer(data):
            if not ID_KEY_BEFORE.search(data[max(0, g.start() - 48):g.start()]):
                bare += 1
        if bare:
            guid_files[where] = bare
    for where, n in list(guid_files.items())[:8]:
        r.warn("90/99", f"{where}: {n} GUID-shaped string(s) not attached to an id field — confirm none is a canary")


def run_all(outer: Path) -> tuple[Report, list[int]]:
    inner = outer / outer.name
    r = Report()
    check_structure(outer, inner, r)
    expected, parametrized = collected_test_count(inner / "tests") if (inner / "tests").is_dir() else (0, False)
    ev_stamps = check_evidence(outer, inner, expected, parametrized, r)
    tr_stamps, rewards = check_trajectories(outer, inner, expected, parametrized, r)
    newest, newest_name = newest_graded_mtime(inner) if inner.is_dir() else (0.0, "")
    if ev_stamps and newest > min(ev_stamps):
        r.err("77", f"graded file {newest_name} is newer than oracle-nop-evidence — regenerate oracle + NOP")
    if tr_stamps and newest > min(tr_stamps):
        r.err("83", f"graded file {newest_name} is newer than trajectories — regenerate everything atomically (check 96)")
    check_gate(rewards, inner, r)
    scrub(outer, r)
    return r, rewards


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    outer = resolve_outer(argv[0])
    print(f"== tb40_ship_check: {outer.name} ==")
    r, _ = run_all(outer)
    for line in r.errors + r.warns:
        print(line)
    print(f"-- {len(r.errors)} error(s), {len(r.warns)} warning(s)")
    print("Manual checks still required (answer them via master_check.py sign-offs), each with evidence.")
    return 1 if r.errors else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
