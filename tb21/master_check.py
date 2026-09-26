#!/usr/bin/env python3
"""Master Ship Checklist runner (checks 0-85) for a TB 2.1 delivery.

Runs tb21_check.py and tb21_ship_check.py, adds automated and assisted analyses
for the remaining checks, and keeps a per-check sign-off so every check ends up
answered with evidence against the current disk state.

Status per check:
  PASS    automated and clean
  FAIL    open finding: fix it (a FAIL cannot be signed off)
  REVIEW  heuristic findings: read them, then fix or sign off with evidence
  MANUAL  needs a human verdict: sign off with evidence
  STALE   signed off, but files the check depends on changed since: re-verify, then --restamp
  SIGNED  signed off with evidence for the current files

Files (outside the delivery folder, never zipped):
  _reports/<slug>/MASTER_REPORT.md   per-check results and evidence appendices
  _reports/<slug>/signoff.toml       your verdicts: status = "pass" | "n/a" | "fail", evidence = "..."
  _reports/<slug>/baselines.json     written by run_baselines.py (check 31)
  _reports/<slug>/ablation.json      written by run_baselines.py --ablate (check 30)

A filled sign-off is bound to the fingerprint of the files its check depends on
the first time it is seen. Evidence must cite something concrete: file:line,
`quoted text`, or a command and its output.

Usage:
    py -3 tb21/master_check.py <slug-dir>                   exit 1 unless every check is PASS/SIGNED
    py -3 tb21/master_check.py <slug-dir> --restamp 27,30   re-bind re-verified STALE sign-offs
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import difflib
import getpass
import hashlib
import io
import json
import posixpath
import re
import sys
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tb21_check as static  # noqa: E402
import tb21_ship_check as ship  # noqa: E402

ROOT = HERE.parent
REPORTS = ROOT / "_reports"
CI = -1

# number -> (section, title, mode, fingerprint scope)
# mode: auto = fully mechanical; assist = heuristics + human verdict; manual = human verdict only
CHECKS: dict[int, tuple[str, str, str, str]] = {
    CI: ("-", "CI / pool static gates (pinned deps, base image, test.sh, docstrings, ruff, diversity)", "auto", "task"),
    0: ("A", "Human-written prompt, absolute paths in backticks, outputs named, < 1500 tokens", "assist", "task"),
    1: ("A", "Every stated requirement is exercised by a test", "assist", "task"),
    2: ("A", "Every requirement a test enforces is stated", "assist", "task"),
    3: ("A", "No implementation-step ('how') sentences", "assist", "task"),
    4: ("A", "Interface contracts named in the prompt are really graded", "manual", "task"),
    5: ("A", "No grader / test-suite / pipeline terms", "auto", "task"),
    6: ("A", "Stated constants match tests byte for byte", "assist", "task"),
    7: ("A", "Every path the prompt names exists in the built image", "auto", "task"),
    8: ("A", "Output schema exactness in prose matches the tests", "assist", "task"),
    9: ("A", "No self-contradiction between sentences", "manual", "task"),
    10: ("A", "Prompt does not narrate each planted defect's mechanism", "assist", "task"),
    11: ("B", "Every environment file is required", "manual", "task"),
    12: ("B", "No BUG/FIXME/planted/intent comments (grep)", "auto", "task"),
    13: ("B", "No comments echoing instruction or rubric text", "assist", "task"),
    14: ("B", "No lore/notes doc indexing the planted defects", "assist", "task"),
    15: ("B", "No opaque short file/module names", "auto", "task"),
    16: ("B", "No names that mislabel behavior", "manual", "task"),
    17: ("B", "No dead / orphaned files", "auto", "task"),
    18: ("B", "No unused module that already implements the answer", "manual", "task"),
    19: ("B", "Authoritative docs consistent with instruction.md", "manual", "task"),
    20: ("B", "Non-authoritative docs hold no hidden graded rule", "manual", "task"),
    21: ("B", "Vendored archives/binaries carry no host metadata", "auto", "task"),
    22: ("B", "Dockerfile never copies solution/ or tests/", "auto", "task"),
    23: ("B", "Decoys are reachable, fair and not labelled", "assist", "task"),
    24: ("C", "solve.sh delta listed file by file", "assist", "task"),
    25: ("C", "Every touched file maps to a requested fix (no no-op delta)", "assist", "task"),
    26: ("C", "No out-of-scope delta", "manual", "task"),
    27: ("C", "Reference output independently re-derived", "manual", "task"),
    28: ("C", "Agent consensus vs reference outlier checked", "manual", "task"),
    29: ("C", "No orphaned files in solution/", "auto", "task"),
    30: ("C", "Each fix ablated alone produces test failures", "auto", "task"),
    31: ("C", "Cold linux/amd64 oracle build runs cleanly", "auto", "task"),
    32: ("D", "Zero individual tests pass under NOP", "auto", "evidence"),
    33: ("D", "Guard-style tests are coupled to real behavior", "assist", "task"),
    34: ("D", "NOP-passable guards coupled, not deleted", "manual", "task"),
    35: ("D", "Assertions do what names/docstrings claim", "assist", "task"),
    36: ("D", "Expected values never computed by agent-editable code", "assist", "task"),
    37: ("D", "Fixtures feeding expected values are not agent-editable", "assist", "task"),
    38: ("D", "Held-out scenarios really change the graded outcome", "manual", "task"),
    39: ("D", "Exactness rules enforced literally (set equality)", "assist", "task"),
    40: ("D", "Test tolerances equal the stated tolerances", "assist", "task"),
    41: ("D", "No string obfuscation in tests", "auto", "task"),
    42: ("D", "No dead test helpers", "auto", "task"),
    43: ("D", "Test names describe what they check", "assist", "task"),
    44: ("D", "Fail-closed tests carry a positive control", "assist", "task"),
    45: ("D", "Evidence test counts match current tests/", "auto", "delivery"),
    46: ("E", 'schema_version = "1.1" is the first line', "auto", "task"),
    47: ("E", "description/keywords/authors/category/tags accurate", "assist", "task"),
    48: ("E", "All timeouts are 7200", "auto", "task"),
    49: ("E", "No reference_pattern / pipeline metadata", "auto", "task"),
    50: ("E", "allow_internet = true and no offline instruction", "auto", "task"),
    51: ("F", "Every rubric line maps to a test or instruction", "assist", "rubric"),
    52: ("F", "Rubric format 'Agent ..., +/-N', no headers/blank lines", "auto", "rubric"),
    53: ("F", "No mutually contradictory rubric lines", "manual", "rubric"),
    54: ("F", "No double-counted behavior", "assist", "rubric"),
    55: ("F", "rubric_score arithmetic consistent with rubric.txt", "auto", "traj"),
    56: ("F", "Rubric cites only mechanisms that exist", "auto", "rubric"),
    57: ("H", "Evidence structure exact", "auto", "evidence"),
    58: ("H", "Oracle x3 full credit, every test passing", "auto", "evidence"),
    59: ("H", "NOP x2 zero credit, every test 'failed'", "auto", "evidence"),
    60: ("H", "NOP failures are genuine assertion mismatches", "auto", "evidence"),
    61: ("H", "Evidence newer than every graded file", "auto", "delivery"),
    62: ("H", "Evidence not duplicated", "auto", "evidence"),
    63: ("G", "SUMMARY.txt exactly 2 lines", "auto", "traj"),
    64: ("G", "rubric_score.txt is pure data + citations", "auto", "traj"),
    65: ("G", "SUMMARY rewards match each run's reward.txt and ctrf", "auto", "traj"),
    66: ("G", "SUMMARY sha matches a fresh recompute", "auto", "delivery"),
    67: ("G", "Trajectories newer than every graded file", "auto", "delivery"),
    68: ("G", "Oracle runs independent", "auto", "evidence"),
    69: ("G", "NOP runs independent", "auto", "evidence"),
    70: ("G", "Each failing run's cause read from its own files", "assist", "traj"),
    71: ("G", "rubric_score files not copies of each other", "auto", "traj"),
    72: ("G", "NOT MET / negative verdicts cite that run's own evidence", "assist", "traj"),
    73: ("G", "MET verdicts spot-checked against the trajectory", "assist", "traj"),
    74: ("G", "PII scrub clean across trajectory files", "auto", "delivery"),
    75: ("G", "config.json paths scrubbed to /terminal-bench2.1/<slug>", "auto", "delivery"),
    76: ("G", "result.json model names left raw", "auto", "delivery"),
    77: ("G", "agent/ file sets identical across runs", "auto", "traj"),
    78: ("G", "verifier/ files present, reward matches ctrf", "auto", "traj"),
    79: ("G", "reasoning_effort xhigh on every run", "auto", "delivery"),
    80: ("G", "No exception_info in any result.json", "auto", "delivery"),
    81: ("G", "Reward-hacking scan on every trajectory", "assist", "traj"),
    82: ("G", "Evidence regenerated atomically after the last k=5", "auto", "delivery"),
    83: ("I", "Difficulty comes from genuine reasoning, source classified", "manual", "task"),
    84: ("I", "Delivery structure exact, no junk", "auto", "delivery"),
    85: ("I", "Final stb / personal-path scrub across the whole bundle", "auto", "delivery"),
}

STATIC_MAP = {
    "defect-tell": [12],
    "decoy-label": [23],
    "naming": [15],
    "unreferenced": [17],
    "tests-in-image": [22],
    "dockerfile-references": [22],
    "obfuscation": [41],
    "dead-code": [42],
    "scrub": [85],
    "delivery": [84],
    "layout": [84],
    "structure": [84],
    "absolute-path": [0],
}
STOP = set(
    "the a an and or of to in on for with by from that this these those is are be been was were it its as at "
    "into than then when which while each every any all not no must should can may will would does do did "
    "agent agents file files using use used only also same other its their there here what where how why".split()
)
DATA_EXT = {".json", ".csv", ".tsv", ".txt", ".yaml", ".yml", ".toml", ".xml", ".dat", ".ini", ".conf", ".cfg", ".log", ".ndjson", ".jsonl"}
TAR_EXT = (".tar", ".tgz", ".tar.gz", ".tar.xz", ".tar.bz2", ".tbz2", ".txz")
ZIP_EXT = {".whl", ".zip", ".jar", ".egg", ".war", ".nupkg"}
SLASH_COMMENT = {".go", ".c", ".h", ".cc", ".cpp", ".hpp", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".rs", ".java",
                 ".kt", ".swift", ".scala", ".cs", ".php", ".dart", ".zig", ".proto", ".groovy", ".gradle"}
HASH_COMMENT = {".py", ".sh", ".bash", ".rb", ".pl", ".toml", ".yaml", ".yml", ".conf", ".ini", ".cfg", ".r", ".mk",
                ".cmake", ".nix", ".tf", ".awk", ".tcl", ".ps1", ".exs", ".ex", ".jl"}
DASH_COMMENT = {".sql", ".lua", ".hs", ".elm", ".ada", ".adb"}
DEFECT_WORDS = re.compile(
    r"\b(bug|fix(ed|es)?|broken|wrong|incorrect|regress\w*|known issue|quirk|mistake|off-by-one|misbehav\w*|fails?|flaw\w*)\b",
    re.I,
)
GRADING_CMD = re.compile(
    r"(?<![\w.])/tests\b|test_outputs\.py|ctrf\.json|/logs/verifier|reward\.txt|/opt/verifier"
    r"|(?<![\w.])/solution\b|(?<![\w.])/oracle\b|\bsolve\.sh\b"
)


@dataclass
class Finding:
    level: str  # error | warn | info
    msg: str


@dataclass
class Touch:
    target: str
    kind: str
    start: int
    end: int
    content: str | None = None


@dataclass
class Ctx:
    outer: Path
    slug: str = ""
    inner: Path = Path()
    env: Path = Path()
    instruction: str = ""
    rubric: list[tuple[str, int]] = field(default_factory=list)
    tests_text: str = ""
    solve: str = ""
    image: ImageMap | None = None
    findings: dict[int, list[Finding]] = field(default_factory=dict)
    appendix: dict[str, list[str]] = field(default_factory=dict)

    def add(self, n: int, level: str, msg: str) -> None:
        self.findings.setdefault(n, []).append(Finding(level, msg))

    def note(self, section: str, line: str) -> None:
        self.appendix.setdefault(section, []).append(line)


# --------------------------------------------------------------------------- helpers


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else []


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def stems(s: str) -> set[str]:
    return {w[:5] for w in words(s) if len(w) >= 4 and w not in STOP}


def sentences(text: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"[^.!?\n]+(?:[.!?](?=\s|$)|\n|$)", text):
        s = m.group(0).strip()
        if len(s) > 3:
            out.append((text.count("\n", 0, m.start()) + 1, s))
    return out


def line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


def fp(paths: list[Path], base: Path, seed: str = "") -> str:
    h = hashlib.sha256(seed.encode())
    for p in sorted(paths, key=lambda q: q.relative_to(base).as_posix()):
        h.update(p.relative_to(base).as_posix().encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()[:16]


def numbers(text: str) -> list[tuple[str, float]]:
    out = []
    for m in re.finditer(r"(?<![\w.])[-+]?(?:\d+\.\d+|\.\d+|\d+)(?:[eE][-+]?\d+)?(?![\w]|\.\d)", text):
        try:
            out.append((m.group(0), float(m.group(0))))
        except ValueError:
            pass
    return out


def num_in(value: float, pool: set[float]) -> bool:
    return any(value == v or (value and abs(value - v) <= abs(value) * 1e-12) for v in pool)


class ImageMap:
    """Maps container paths to environment/ sources using the Dockerfile's WORKDIR/COPY/ADD lines."""

    def __init__(self, env: Path) -> None:
        self.env = env
        self.copies: list[tuple[str, Path, bool]] = []
        self.run_text = ""
        self.workdir = "/"
        df = env / "Dockerfile"
        if not df.is_file():
            return
        wd = "/"
        for op, args in static.dockerfile_instructions(read(df)):
            if op == "WORKDIR":
                wd = posixpath.normpath(posixpath.join(wd, args.strip().strip("\"'")))
            elif op in {"COPY", "ADD"}:
                if "--from" in args:
                    continue
                toks = [t.strip("\"'[],") for t in args.split() if not t.startswith("--")]
                if len(toks) < 2:
                    continue
                *srcs, dest = toks
                dest_abs = posixpath.normpath(posixpath.join(wd, dest))
                dir_dest = dest.endswith("/") or len(srcs) > 1
                for s in srcs:
                    for src in (sorted(env.glob(s)) if any(c in s for c in "*?[") else [env / s]):
                        self.copies.append((dest_abs, src, dir_dest))
            elif op == "RUN":
                self.run_text += args + "\n"
        self.workdir = wd

    def to_env(self, cp: str) -> Path | None:
        cp = posixpath.normpath(cp)
        for dest, src, dir_dest in reversed(self.copies):
            if src.is_dir():
                if cp == dest:
                    return src
                prefix = dest.rstrip("/") + "/"
                if cp.startswith(prefix) and (src / cp[len(prefix):]).exists():
                    return src / cp[len(prefix):]
            elif src.is_file():
                if cp == posixpath.join(dest, src.name) or (cp == dest and not dir_dest):
                    return src
        return None

    def resolve(self, cp: str) -> str | None:
        hit = self.to_env(cp)
        if hit is not None:
            return f"environment/{hit.relative_to(self.env).as_posix()}" if hit != self.env else "environment/"
        norm = posixpath.normpath(cp)
        if any(dest == norm or dest.startswith(norm.rstrip("/") + "/") for dest, _, _ in self.copies):
            return "directory in image"
        if norm == self.workdir or re.search(rf"(?<![\w/]){re.escape(norm)}(?![\w.-])", self.run_text):
            return "created by a Dockerfile RUN step"
        return None


def abs_paths(text: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"(?<![\w.:/~$-])(/(?:[\w.@+-]+/?)+)", text):
        p = m.group(1).rstrip(".,;:)/") or "/"
        if re.search(r"[A-Za-z]", p) and p not in out and not re.match(r"/[A-Za-z]$", p):
            out.append(p)
    return out


# --------------------------------------------------------------------------- solution parsing


def parse_solve(text: str, workdir: str) -> list[Touch]:
    lines = text.split("\n")
    touches: list[Touch] = []
    cwd = workdir
    i = 0
    while i < len(lines):
        ln, s = lines[i], lines[i].strip()
        m = re.match(r"cd\s+([^\s;&|]+)", s)
        if m and "$" not in m.group(1):
            cwd = posixpath.normpath(posixpath.join(cwd, m.group(1).strip("\"'")))
        hd = re.search(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2", ln) if not s.startswith("#") else None
        if hd:
            delim, dash = hd.group(3), hd.group(1)
            j, body = i + 1, []
            while j < len(lines) and (lines[j].lstrip("\t") if dash else lines[j]).rstrip() != delim:
                body.append(lines[j])
                j += 1
            rest = ln[: hd.start()] + ln[hd.end():]
            tgt = re.search(r"(?<![0-9&>])>>?\s*([^\s;|&<>]+)", rest) or re.search(r"\btee\s+(?:-a\s+)?([^\s;|&<>]+)", rest)
            content = "\n".join(body)
            if tgt and tgt.group(1) != "/dev/null":
                touches.append(Touch(posixpath.normpath(posixpath.join(cwd, tgt.group(1).strip("\"'"))), "heredoc", i + 1, j + 1, content))
            elif re.search(r"\b(git\s+apply|patch)\b", rest):
                for f in sorted(set(re.findall(r"^\+\+\+ (?:b/)?(\S+)", content, re.M))):
                    touches.append(Touch(posixpath.normpath(posixpath.join(cwd, f)), "patch", i + 1, j + 1))
            else:
                touches.append(Touch(f"(inline script at solve.sh:{i + 1})", "script", i + 1, j + 1, content))
            i = j + 1
            continue
        m = re.match(r"sed\s+(?:-\S*i\S*|--in-place\S*)\s+.*\s([^\s;|&]+)$", s)
        if m:
            touches.append(Touch(posixpath.normpath(posixpath.join(cwd, m.group(1).strip("\"'"))), "sed", i + 1, i + 1))
        m = re.match(r"(cp|mv|install)\s+(?:-\S+\s+)*([^\s;|&]+)\s+([^\s;|&]+)$", s)
        if m:
            dest = posixpath.normpath(posixpath.join(cwd, m.group(3).strip("\"'")))
            touches.append(Touch(dest, m.group(1), i + 1, i + 1, m.group(2)))
        i += 1
    return touches


def ablation_units(touches: list[Touch]) -> dict[str, list[Touch]]:
    units: dict[str, list[Touch]] = {}
    for t in touches:
        units.setdefault(t.target, []).append(t)
    return units


# --------------------------------------------------------------------------- analyses: instruction


def check_instruction(ctx: Ctx) -> None:
    text = ctx.instruction
    if not text or ctx.image is None:
        return
    tests_blob = ctx.tests_text + "\n" + ctx.solve
    for p in abs_paths(text):
        if any(c in p for c in "*<>{}"):
            continue
        where = ctx.image.resolve(p)
        ln = line_of(text, p)
        if where:
            ctx.note("Instruction paths (check 7)", f"`{p}` (instruction.md:{ln}) -> {where}")
        elif p in tests_blob:
            ctx.note("Instruction paths (check 7)", f"`{p}` (instruction.md:{ln}) -> output path, referenced by tests/ or solve.sh")
        else:
            near = [f.relative_to(ctx.env).as_posix() for f in files(ctx.env) if f.name == posixpath.basename(p)]
            hint = f"; same basename exists at environment/{near[0]}" if near else ""
            ctx.add(7, "warn", f"instruction.md:{ln} names `{p}`, which is not in the image and not used by tests/solve.sh{hint}")
            ctx.note("Instruction paths (check 7)", f"`{p}` (instruction.md:{ln}) -> NOT FOUND{hint}")

    stripped = re.sub(r"https?://\S+|(?<![\w.])/(?:[\w.@+-]+/?)+", " ", text)
    stripped = re.sub(r"(?i)\b(rfc|iso|ieee|section|version|v|python|go|node|java|ruby|rust|posix|utf|sha|md|x86|arm)[\s-]?\d[\d.]*", " ", stripped)
    test_nums = {v for _, v in numbers(ctx.tests_text)}
    for raw, v in numbers(stripped):
        if v.is_integer() and 0 <= v <= 10:
            continue
        ln = line_of(text, raw)
        if num_in(v, test_nums):
            ctx.note("Stated constants (checks 6, 40)", f"instruction.md:{ln} `{raw}` -> present in tests/")
        else:
            ctx.add(6, "warn", f"instruction.md:{ln} states `{raw}` but no equal literal exists in tests/ - confirm it is enforced or purely illustrative")
            ctx.note("Stated constants (checks 6, 40)", f"instruction.md:{ln} `{raw}` -> NOT in tests/")

    exact = re.compile(r"\bexactly\b|\bonly (these|the following)\b|\bno (other|extra|additional)\b|\bnothing else\b|\bunique\b", re.I)
    set_eq = re.compile(r"set\([^)]*\)\s*==|==\s*set\(|sorted\([^)]*\)\s*==|==\s*sorted\(|\.keys\(\)\)?\s*==|==\s*\{|==\s*\[|assert_frame_equal|assertCountEqual|assertEqual\(\s*set")
    for ln, s in sentences(text):
        if exact.search(s):
            if set_eq.search(ctx.tests_text):
                ctx.add(8, "info", f"instruction.md:{ln} exactness rule: \"{s[:120]}\" - tests contain equality checks; confirm they cover this rule")
                ctx.add(39, "info", f"instruction.md:{ln} \"{s[:120]}\" - confirm the test uses set/list equality for it and solve.sh satisfies it")
            else:
                ctx.add(8, "warn", f"instruction.md:{ln} exactness rule \"{s[:120]}\" but tests/ show no set/list equality assertion")
                ctx.add(39, "warn", f"instruction.md:{ln} \"{s[:120]}\" - no literal equality enforcement found in tests/")

    how = [
        r"\buse (a|an|the)\s+(\w+\s+){0,2}(algorithm|data structure|hash ?map|dict(ionary)?|heap|queue|stack|regex|library|package)\b",
        r"\breplace (the )?line\b",
        r"\bchange\s+`[^`]+`\s+to\s+`",
        r"\bline \d+\b",
        r"\b(add|insert) (a |an )?(call|line|variable|field) (named|called|to)\b",
        r"\bin (the )?function\s+`",
        r"\bcall\s+`[^`]+`\s+(before|after|instead)\b",
        r"\bshould (loop|iterate|recurse)\b",
    ]
    narrate = [
        r"\bthe (bug|defect|problem|issue) is\b",
        r"\bis caused by\b",
        r"\bforgets? to\b",
        r"\boff-by-one\b",
        r"\bchange[sd]? from\b.*\bto\b",
        r"\bbecause (it|the code|the function)\b",
    ]
    for ln, s in sentences(text):
        if any(re.search(rx, s, re.I) for rx in how):
            ctx.add(3, "warn", f"instruction.md:{ln} reads like an implementation step: \"{s[:140]}\" - reword as an outcome unless it is a graded interface (check 4)")
        if any(re.search(rx, s, re.I) for rx in narrate):
            ctx.add(10, "warn", f"instruction.md:{ln} may narrate a defect's mechanism: \"{s[:140]}\"")


# --------------------------------------------------------------------------- analyses: environment


def comment_blocks(path: Path, text: str) -> list[tuple[int, str]]:
    suffix = path.suffix.lower()
    style = (
        "slash" if suffix in SLASH_COMMENT
        else "hash" if suffix in HASH_COMMENT or path.name in {"Dockerfile", "Makefile", "makefile", "GNUmakefile"}
        else "dash" if suffix in DASH_COMMENT
        else None
    )
    if style is None:
        return []
    blocks: list[tuple[int, str]] = []
    cur: list[str] = []
    start = 0
    in_block = False
    for n, line in enumerate(text.splitlines(), 1):
        piece = None
        if style == "slash":
            if in_block:
                end = line.find("*/")
                piece = line[: end if end >= 0 else None].strip(" *")
                in_block = end < 0
            elif (m := re.search(r"(?<![:\"'])//+\s?(.*)$", line)):
                piece = m.group(1)
            elif (m := re.search(r"/\*+(.*?)(\*/|$)", line)):
                piece = m.group(1).strip(" *")
                in_block = m.group(2) != "*/"
        elif style == "hash":
            if not line.startswith("#!") and (m := re.search(r"(?:^|\s)#+\s?(.*)$", line)):
                piece = m.group(1)
        elif (m := re.search(r"--+\s?(.*)$", line)):
            piece = m.group(1)
        if piece is not None:
            if not cur:
                start = n
            cur.append(piece)
        elif cur:
            blocks.append((start, " ".join(cur)))
            cur = []
    if cur:
        blocks.append((start, " ".join(cur)))
    return blocks


def ngrams(ws: list[str], k: int = 6) -> set[tuple[str, ...]]:
    return {tuple(ws[i:i + k]) for i in range(len(ws) - k + 1)}


def check_environment(ctx: Ctx) -> None:
    author = ctx.instruction + "\n" + "\n".join(body for body, _ in ctx.rubric)
    author_grams = ngrams(words(author))
    author_sents = [(s, stems(s)) for _, s in sentences(author) if len(stems(s)) >= 6]
    user = getpass.getuser().lower()
    host_rx = re.compile(rb"/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\\\?Users\\\\?|/home/(?!agent\b|app\b|user\b|ubuntu\b|runner\b|node\b|root\b)[A-Za-z0-9_.-]+/")
    for p in files(ctx.env):
        rel = p.relative_to(ctx.env).as_posix()
        data = p.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is None:
            scan_binary(ctx, rel, p, data, host_rx, user)
            continue
        for ln, block in comment_blocks(p, text):
            bw = words(block)
            hit = ngrams(bw) & author_grams
            if hit:
                ctx.add(13, "warn", f"environment/{rel}:{ln} comment repeats author text \"{' '.join(next(iter(hit)))}\"")
                continue
            bs = stems(block)
            if len(bs) >= 6:
                for s, ss in author_sents:
                    overlap = len(bs & ss) / len(bs | ss)
                    if overlap >= 0.6:
                        ctx.add(13, "warn", f"environment/{rel}:{ln} comment closely paraphrases \"{s[:100]}\" ({overlap:.0%} word overlap)")
                        break
        if p.suffix.lower() in {".md", ".txt", ".rst", ".adoc"} or p.stem.upper() in {"NOTES", "HISTORY", "CHANGELOG", "TODO", "LORE"}:
            bullets = [(n, ln) for n, ln in enumerate(text.splitlines(), 1) if re.match(r"\s*(?:[-*+]|\d+[.)])\s", ln) and DEFECT_WORDS.search(ln)]
            if len(bullets) >= 3:
                sample = "; ".join(f"{n}: {ln.strip()[:60]}" for n, ln in bullets[:3])
                ctx.add(14, "warn", f"environment/{rel} has {len(bullets)} bullet lines using defect vocabulary - confirm it is not an index of the planted defects ({sample})")


def scan_binary(ctx: Ctx, rel: str, p: Path, data: bytes, host_rx: re.Pattern[bytes], user: str) -> None:
    name = p.name.lower()
    try:
        if name.endswith(TAR_EXT):
            tar_owner_check(ctx, rel, data)
        elif p.suffix.lower() in ZIP_EXT:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for info in zf.infolist()[:5000]:
                    if info.file_size < 5 * 1024 * 1024:
                        inner = zf.read(info)
                        if host_rx.search(inner):
                            ctx.add(21, "error", f"environment/{rel}!{info.filename} contains a host path")
                            break
        elif name.endswith(".deb") and data.startswith(b"!<arch>\n"):
            pos = 8
            while pos + 60 <= len(data):
                hdr = data[pos:pos + 60]
                mname = hdr[:16].decode(errors="replace").strip().rstrip("/")
                size = int(hdr[48:58].decode().strip() or 0)
                body = data[pos + 60:pos + 60 + size]
                if mname.startswith(("data.tar", "control.tar")):
                    tar_owner_check(ctx, f"{rel}!{mname}", body)
                pos += 60 + size + (size % 2)
    except (tarfile.TarError, zipfile.BadZipFile, ValueError, EOFError, OSError) as exc:
        ctx.add(21, "warn", f"environment/{rel}: could not inspect archive ({exc})")
    m = host_rx.search(data)
    if m:
        ctx.add(21, "error", f"environment/{rel} embeds host path {m.group(0).decode(errors='replace')}")
    if len(user) >= 4 and re.search(rb"(?i)\b" + re.escape(user.encode()) + rb"\b", data):
        ctx.add(21, "error", f"environment/{rel} embeds the local username '{user}'")


def tar_owner_check(ctx: Ctx, rel: str, data: bytes) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
        for m in tf.getmembers():
            if m.uname not in ("", "root") or m.gname not in ("", "root"):
                ctx.add(21, "error", f"environment/{rel}: tar member {m.name} owned by {m.uname}:{m.gname} - re-tar with --owner=0 --group=0")
                return
            if m.uid or m.gid:
                ctx.add(21, "warn", f"environment/{rel}: tar member {m.name} has uid/gid {m.uid}/{m.gid} - prefer --owner=0 --group=0")
                return


# --------------------------------------------------------------------------- analyses: solution


def check_solution(ctx: Ctx) -> list[Touch]:
    sol = ctx.inner / "solution"
    if not ctx.solve or ctx.image is None:
        return []
    for f in files(sol):
        if f.name == "solve.sh":
            continue
        rel = f.relative_to(sol).as_posix()
        if f.name not in ctx.solve and rel not in ctx.solve:
            ctx.add(29, "error", f"solution/{rel} is never referenced by solve.sh - wire it in or delete it")
    touches = parse_solve(ctx.solve, ctx.image.workdir)
    if not touches:
        ctx.add(24, "warn", "no file writes recognised in solve.sh (heredoc/sed -i/cp/patch) - list the delta by hand")
    instr_low = ctx.instruction
    for target, group in ablation_units(touches).items():
        lines = ", ".join(f"{t.start}-{t.end}" if t.end != t.start else str(t.start) for t in group)
        kinds = "/".join(sorted({t.kind for t in group}))
        orig = ctx.image.to_env(target) if not target.startswith("(") else None
        if orig is not None and orig.is_dir():
            orig = None
        desc = f"`{target}` via {kinds} at solve.sh:{lines}"
        heredocs = [t for t in group if t.kind == "heredoc" and t.content is not None]
        if orig is None:
            ctx.note("Solution delta (checks 24-26, 30)", f"{desc} -> new file / not shipped in environment/")
            continue
        old = read(orig)
        rel = orig.relative_to(ctx.env).as_posix()
        if heredocs:
            new = heredocs[-1].content + "\n"
            if new == old or new.rstrip("\n") == old.rstrip("\n"):
                ctx.add(25, "error", f"{desc} writes content identical to environment/{rel} - no-op delta")
                ctx.note("Solution delta (checks 24-26, 30)", f"{desc} -> NO-OP (identical to environment/{rel})")
                continue
            diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0))
            added = [d[1:] for d in diff if d.startswith("+") and not d.startswith("+++")]
            removed = [d[1:] for d in diff if d.startswith("-") and not d.startswith("---")]
            ctx.note("Solution delta (checks 24-26, 30)", f"{desc} -> environment/{rel}: +{len(added)} / -{len(removed)} lines")
            new_ids = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", "\n".join(added))) - set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", old))
            named = sorted(x for x in new_ids if re.search(r"[a-z][A-Z]|_", x) and re.search(rf"\b{re.escape(x)}\b", instr_low))
            if named:
                ctx.add(10, "warn", f"instruction.md names identifiers the fix introduces in environment/{rel}: {', '.join(named[:6])} - it may hand over the fix")
        else:
            ctx.note("Solution delta (checks 24-26, 30)", f"{desc} -> environment/{rel}")
    return touches


# --------------------------------------------------------------------------- analyses: tests


def test_functions(ctx: Ctx) -> list[tuple[Path, ast.FunctionDef, str, str]]:
    out = []
    for path in sorted((ctx.inner / "tests").rglob("*.py")):
        src = read(path)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        nodes: list[ast.AST] = []
        for node in tree.body:
            nodes.extend(node.body if isinstance(node, ast.ClassDef) and node.name.startswith("Test") else [node])
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                out.append((path, node, ast.get_docstring(node) or "", ast.get_source_segment(src, node) or ""))
    return out


def check_tests(ctx: Ctx) -> None:
    tdir = ctx.inner / "tests"
    fns = test_functions(ctx)
    guard_name = re.compile(r"pristine|unchanged|untouched|intact|unmodified|integrity|read_?only|tamper|guard|preserved", re.I)
    guard_doc = re.compile(
        r"\b(inputs?|fixtures?|data|sources?|files?|originals?|shipped \w+)\b[^.]{0,40}\b(pristine|unchanged|untouched|intact|unmodified|not (been )?(modified|altered|tampered))\b",
        re.I,
    )
    rej = re.compile(r"returncode\s*(!=|>)\s*0|\bpytest\.raises\b|returncode\s+not\s+in\s*[(\[{]\s*0|!=\s*0\b")
    pos = re.compile(r"returncode\s*==\s*0|check\s*=\s*True|\.check_returncode\(\)|returncode\s+in\s*[(\[{]\s*0|==\s*0\b")
    for path, node, doc, seg in fns:
        where = f"tests/{path.relative_to(tdir).as_posix()}:{node.lineno} {node.name}"
        body = "\n".join(seg.splitlines()[1:])
        if guard_name.search(node.name) or guard_doc.search(doc):
            ctx.add(33, "warn", f"{where} looks like a guard test - confirm it is coupled to a real-behavior assertion in the same function")
        if rej.search(body) and not pos.search(body):
            ctx.add(44, "warn", f"{where} asserts a rejection/non-zero exit with no positive control in the same function")
        toks = [t for t in node.name.split("_")[1:] if len(t) >= 4 and t not in STOP]
        text = (doc + "\n" + body).lower()
        missing = [t for t in toks if t[:5] not in text]
        if toks and len(missing) > len(toks) / 2:
            ctx.add(43, "warn", f"{where}: name words {missing} do not appear in its docstring/body - confirm the name describes the check")
        ctx.note("Tests (checks 35, 43)", f"{where} - {doc.splitlines()[0][:110] if doc else '(no docstring)'}")

    for path in sorted(tdir.rglob("*.py")):
        src = read(path)
        rel = f"tests/{path.relative_to(tdir).as_posix()}"
        for m in re.finditer(r"sys\.path\.(insert|append)\([^)]*['\"](/[^'\"]*)['\"]", src):
            ctx.add(36, "warn", f"{rel}:{line_of(src, m.group(0))} imports code from {m.group(2)} - expected values must not come from agent-editable code")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and re.search(r"expect|want|golden|truth|reference", t.id, re.I) for t in node.targets):
                seg = ast.get_source_segment(src, node.value) or ""
                if re.search(r"subprocess|check_output|Popen|os\.system|run_cli|run\(", seg):
                    ctx.add(36, "warn", f"{rel}:{node.lineno} expected value computed by running a program: {seg[:90]}")
        if ctx.image is not None:
            seen: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("/") and node.value not in seen:
                    seen.add(node.value)
                    hit = ctx.image.to_env(node.value)
                    if hit is not None and hit.is_file() and hit.suffix.lower() in DATA_EXT:
                        ctx.add(37, "warn", f"{rel}:{node.lineno} reads `{node.value}` (agent-editable, from environment/{hit.relative_to(ctx.env).as_posix()}) - confirm it never feeds the expected side")

    tol: list[tuple[str, int, float]] = []
    for path in sorted(tdir.rglob("*.py")):
        src = read(path)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        rel = f"tests/{path.relative_to(tdir).as_posix()}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fname = ast.unparse(node.func)
                if re.search(r"approx|isclose|allclose|assertAlmostEqual", fname):
                    for kw in node.keywords:
                        if kw.arg in {"abs", "rel", "rtol", "atol", "delta"} and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, (int, float)):
                            tol.append((rel, node.lineno, float(kw.value.value)))
            elif isinstance(node, ast.Compare) and isinstance(node.left, ast.Call) and ast.unparse(node.left.func) in {"abs", "math.fabs"}:
                for op, comp in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Lt, ast.LtE)) and isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                        tol.append((rel, node.lineno, float(comp.value)))
    stated = {v for _, v in numbers(ctx.instruction)}
    for doc in files(ctx.env):
        if doc.suffix.lower() in {".md", ".txt", ".rst"}:
            stated |= {v for _, v in numbers(read(doc))}
    for rel, ln, v in tol:
        if num_in(v, stated):
            ctx.note("Stated constants (checks 6, 40)", f"{rel}:{ln} tolerance {v:g} -> stated in instruction/docs")
        else:
            ctx.add(40, "warn", f"{rel}:{ln} enforces tolerance {v:g}, which instruction.md and environment docs never state")


# --------------------------------------------------------------------------- analyses: task.toml / rubric


def check_toml_text(ctx: Ctx) -> None:
    try:
        data = tomllib.loads(read(ctx.inner / "task.toml"))
        skel = tomllib.loads(read(HERE / "skeleton" / "task" / "task.toml"))
    except tomllib.TOMLDecodeError:
        return
    task, stask = data.get("task", {}), skel.get("task", {})
    meta, smeta = data.get("metadata", {}), skel.get("metadata", {})
    for key, cur, tmpl in (("description", task.get("description"), stask.get("description")),
                           ("keywords", task.get("keywords"), stask.get("keywords")),
                           ("tags", meta.get("tags"), smeta.get("tags"))):
        if cur and cur == tmpl:
            ctx.add(47, "error", f"task.toml {key} is still the skeleton value")
    desc = str(task.get("description", ""))
    if desc and len(stems(desc) & stems(ctx.instruction)) < 2:
        ctx.add(47, "warn", f"task.toml description shares almost no words with instruction.md: \"{desc[:100]}\" - stale draft?")


def check_rubric(ctx: Ctx) -> None:
    if not ctx.rubric:
        return
    fns = test_functions(ctx)
    tests = [(n.name, stems(n.name.replace("_", " ") + " " + doc)) for _, n, doc, _ in fns]
    sents = [(ln, s, stems(s)) for ln, s in sentences(ctx.instruction)]
    for body, pts in ctx.rubric:
        bs = stems(body)
        bt = max(tests, key=lambda t: len(bs & t[1]), default=("", set()))
        bi = max(sents, key=lambda s: len(bs & s[2]), default=(0, "", set()))
        ot, oi = len(bs & bt[1]), len(bs & bi[2])
        ctx.note("Rubric map (checks 51, 54)", f"`{body[:90]}` ({pts:+d}) -> test `{bt[0]}` ({ot} shared words); instruction.md:{bi[0]} ({oi})")
        if ot < 2 and oi < 2:
            ctx.add(51, "warn", f"rubric line \"{body[:100]}\" maps to no test and no instruction sentence - confirm what grades it")
        for p in abs_paths(body):
            if ctx.image is not None and not ctx.image.resolve(p) and p not in ctx.instruction and p not in ctx.tests_text:
                ctx.add(56, "warn", f"rubric line cites `{p}`, which exists nowhere in the image, instruction or tests")
    bodies = [b for b, _ in ctx.rubric]
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
            if ratio >= 0.8:
                ctx.add(54, "warn", f"rubric lines are {ratio:.0%} similar - possible double count: \"{a[:70]}\" / \"{b[:70]}\"")


# --------------------------------------------------------------------------- analyses: trajectories


def walk_strings(obj: object, out: list[str]) -> None:
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            walk_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            walk_strings(v, out)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def quote_in(q: str, corpus: str) -> bool:
    variants = {norm(q), norm(q.replace('\\"', '"').replace("\\'", "'")), norm(q.replace("\\n", "\n").replace("\\t", "\t"))}
    return any(v and v in corpus for v in variants)


def parse_score(text: str) -> tuple[list[tuple[str, str, str, str]], tuple[int, int] | None]:
    rows, total = [], None
    for ln in text.splitlines():
        parts = [p.strip() for p in ln.split(" | ")]
        if not parts[0]:
            continue
        if parts[0].lower() == "total":
            m = re.search(r"(-?\d+)\s*/\s*(\d+)", ln)
            total = (int(m.group(1)), int(m.group(2))) if m else None
        elif len(parts) >= 3 and parts[1].upper() in {"MET", "NOT MET"}:
            rows.append((parts[0], parts[1].upper(), parts[2], " | ".join(parts[3:])))
    return rows, total


def check_trajectories(ctx: Ctx) -> None:
    traj = ctx.outer / "trajectories"
    if not traj.is_dir():
        return
    rubric = {body: pts for body, pts in ctx.rubric}
    for run in ship.RUNS:
        d = traj / run
        if not d.is_dir():
            continue
        corpus_parts: list[str] = []
        tj = d / "agent" / "trajectory.json"
        steps: list[dict] = []
        if tj.is_file():
            try:
                data = json.loads(read(tj))
                steps = data.get("steps", []) if isinstance(data, dict) else []
                walk_strings(data, corpus_parts)
            except json.JSONDecodeError:
                ctx.add(81, "error", f"{run}: agent/trajectory.json is not valid JSON")
        for extra in ("verifier/test-stdout.txt", "agent/terminus_2.pane"):
            corpus_parts.append(read(d / extra))
        failed: list[str] = []
        ctrf = d / "verifier" / "ctrf.json"
        if ctrf.is_file():
            try:
                tests, _ = ship.ctrf_tests(json.loads(read(ctrf)))
                failed = [str(t.get("name", "")).split("::")[-1] for t in tests if t.get("status") != "passed"]
                walk_strings(tests, corpus_parts)
            except json.JSONDecodeError:
                pass
        corpus = norm("\n".join(corpus_parts))

        hits = []
        for st in steps:
            for call in st.get("tool_calls") or []:
                keys = str((call.get("arguments") or {}).get("keystrokes", ""))
                m = GRADING_CMD.search(keys)
                if m:
                    hits.append(f"step {st.get('step_id')}: `{norm(keys)[:100]}`")
        for h in hits[:5]:
            ctx.add(81, "error", f"{run}: agent command touches grading/solution paths - {h}")
        calls = [c for st in steps for c in (st.get("tool_calls") or [])]
        if steps and (not calls or calls[-1].get("function_name") != "mark_task_complete"):
            ctx.add(81, "warn", f"{run}: trajectory does not end with mark_task_complete - confirm a genuine completion, not a crash/abandon")
        ctx.note("Runs (checks 70, 81)", f"{run}: {len(steps)} steps, grading-path commands: {len(hits)}, failed tests: {', '.join(failed) or 'none'}")

        rs = d / "rubric_score.txt"
        if not rs.is_file():
            continue
        text = read(rs)
        rows, total = parse_score(text)
        if not rows:
            ctx.add(55, "warn", f"{run}/rubric_score.txt: format not recognised (`criterion | MET/NOT MET | points | evidence`) - verify arithmetic by hand")
        else:
            got = [r[0] for r in rows]
            for body in rubric:
                if body not in got:
                    ctx.add(55, "error", f"{run}/rubric_score.txt is missing rubric line \"{body[:80]}\"")
            for crit in got:
                if crit not in rubric:
                    ctx.add(55, "error", f"{run}/rubric_score.txt has a criterion not in rubric.txt: \"{crit[:80]}\"")
            s, pos_total = 0, sum(p for p in rubric.values() if p > 0)
            for crit, verdict, pts, ev in rows:
                want = rubric.get(crit)
                try:
                    val = int(re.sub(r"[^-+0-9]", "", pts) or "0")
                except ValueError:
                    val = None
                if want is not None:
                    expect = want if verdict == "MET" else 0
                    if val != expect:
                        ctx.add(55, "error", f"{run}/rubric_score.txt \"{crit[:60]}\" {verdict} scores {pts}, expected {expect:+d}")
                s += val or 0
                negative = want is not None and want < 0
                quotes = re.findall(r"`([^`]+)`", ev)
                cited = quotes or re.search(r"\S+:\d+", ev)
                if verdict == "NOT MET" or negative:
                    if not cited:
                        ctx.add(72, "error", f"{run}: \"{crit[:60]}\" {verdict} cites no quote or file:line")
                elif not cited:
                    ctx.add(73, "warn", f"{run}: MET \"{crit[:60]}\" cites no quote from the run")
                missing = [q for q in quotes if not quote_in(q, corpus)]
                for q in missing[:2]:
                    n = 72 if (verdict == "NOT MET" or negative) else 73
                    ctx.add(n, "warn", f"{run}: quote `{q[:80]}` (\"{crit[:40]}\") not found in this run's trajectory/verifier files")
            if total is None:
                ctx.add(55, "error", f"{run}/rubric_score.txt has no 'Total | x / y' line")
            elif total != (s, pos_total):
                ctx.add(55, "error", f"{run}/rubric_score.txt Total {total[0]} / {total[1]}, recomputed {s} / {pos_total}")
        if failed and not any(f in text for f in failed):
            ctx.add(70, "warn", f"{run} failed {failed[:4]} but rubric_score.txt names none of them - confirm the stated failure cause from the run's own files")
        if ctrf.is_file() and rs.stat().st_mtime < ctrf.stat().st_mtime:
            ctx.add(82, "warn", f"{run}/rubric_score.txt is older than its verifier/ctrf.json - was it rewritten for this run?")

        res = d / "result.json"
        if res.is_file():
            try:
                r = json.loads(read(res))
            except json.JSONDecodeError:
                continue
            cm = ((r.get("config") or {}).get("agent") or {}).get("model_name")
            im = ((r.get("agent_info") or {}).get("model_info") or {}).get("name")
            for label, v in (("config.agent.model_name", cm), ("agent_info.model_info.name", im)):
                if v and "@openai/" not in str(v):
                    ctx.add(76, "warn", f"{run}/result.json {label} = {v!r} - raw harbor output keeps '@openai/'; was it hand-edited?")


# --------------------------------------------------------------------------- analyses: baselines / ablation


def check_run_records(ctx: Ctx, sha: str, touches: list[Touch]) -> None:
    rep = REPORTS / ctx.slug
    b = rep / "baselines.json"
    if b.is_file():
        data = json.loads(read(b))
        if data.get("bundle_sha") != sha:
            ctx.add(31, "warn", f"baselines.json is for bundle {data.get('bundle_sha')}, current is {sha} - rerun run_baselines.py")
        elif not data.get("accepted"):
            bad = [f"{r['name']}={r.get('reward')}" for r in data.get("runs", []) if not r.get("ok")]
            ctx.add(31, "error", f"last baseline run was not clean: {bad}")
        elif not data.get("cold_build") or data.get("platform") != "linux/amd64":
            ctx.add(31, "warn", "baselines.json does not record a cold linux/amd64 build")
        else:
            ctx.add(31, "info", f"cold linux/amd64 oracle x3 + nop x2 clean on {data.get('finished_at')} (baselines.json)")
    else:
        ctx.add(31, "info", "no baselines.json - run `py -3 tb21/run_baselines.py <slug>` to automate this check")

    a = rep / "ablation.json"
    if a.is_file():
        data = json.loads(read(a))
        if data.get("bundle_sha") != sha:
            ctx.add(30, "warn", f"ablation.json is for bundle {data.get('bundle_sha')}, current is {sha} - rerun run_baselines.py --ablate")
            return
        done = {u["target"] for u in data.get("units", [])}
        for u in data.get("units", []):
            if not u.get("ok"):
                ctx.add(30, "error", f"ablating {u['target']} left reward {u.get('reward')} / failed tests {u.get('failed_tests')} - the fix is inert or mis-scoped{' (' + u['error'] + ')' if u.get('error') else ''}")
            else:
                ctx.note("Ablation (check 30)", f"`{u['target']}` removed -> reward {u['reward']}, failing: {', '.join(u['failed_tests'])}")
        for t in sorted({t.target for t in touches} - done):
            ctx.add(30, "warn", f"{t} is written by solve.sh but was not ablated")
    else:
        ctx.add(30, "info", "no ablation.json - run `py -3 tb21/run_baselines.py <slug> --ablate` to automate this check")


# --------------------------------------------------------------------------- ingest existing gates


LINE = re.compile(r"^(ERROR|WARN)\s*\[([^\]]+)\]\s*(.*)$")


def map_static(code: str, msg: str) -> list[int]:
    m = re.search(r"ship check (\d+)", msg)
    if m:
        return [int(m.group(1))]
    if code in STATIC_MAP:
        return STATIC_MAP[code]
    if code == "instruction":
        if re.search(r"grading tooling|mentions tests", msg):
            return [5]
        if "offline" in msg:
            return [50]
        if re.search(r"hint|step-by-step", msg):
            return [3, 10]
        return [0]
    if code == "toml":
        if "reference_pattern" in msg:
            return [49]
        if "timeout" in msg:
            return [48]
        if "allow_internet" in msg:
            return [50]
        if "schema_version" in msg or "'version'" in msg:
            return [46]
        if re.search(r"description|keywords|authors", msg):
            return [47]
    if code == "rubric":
        return [54] if "duplicate" in msg else [52]
    return [CI]


def map_ship(code: str, msg: str) -> list[int]:
    nums = [int(x) for x in re.findall(r"\d+", code)]
    return nums or [CI]


def ingest(ctx: Ctx, lines: list[str], mapper) -> None:
    for line in lines:
        m = LINE.match(line)
        if not m:
            continue
        level = "error" if m.group(1) == "ERROR" else "warn"
        for n in mapper(m.group(2), m.group(3)):
            ctx.add(n, level, f"[{m.group(2)}] {m.group(3)}")


# --------------------------------------------------------------------------- sign-off


def load_signoff(path: Path) -> dict[int, dict]:
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"{path}: invalid TOML ({exc}) - fix it before rerunning")
    out = {}
    for key, v in data.items():
        m = re.fullmatch(r"c(\d+|ci)", key)
        if m and isinstance(v, dict):
            out[CI if m.group(1) == "ci" else int(m.group(1))] = v
    return out


def evidence_ok(ev: str) -> bool:
    ev = ev.strip()
    return len(ev) >= 20 and bool(re.search(r"`[^`]+`|\S+:\d+|\"[^\"]{4,}\"|\$ \S+|\b(grep|rg|harbor|diff|find)\b", ev))


def tq(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def write_signoff(path: Path, ctx: Ctx, signoff: dict[int, dict], statuses: dict[int, str], sha: str) -> None:
    out = [
        f"# Master Ship Checklist sign-off - {ctx.slug}",
        f"# Generated by tb21/master_check.py; bundle sha {sha}. Only status/evidence are yours to edit.",
        '# status = "pass" (verified clean), "n/a" (does not apply - say why), "fail" (open finding).',
        "# evidence must cite file:line, `quoted text`, or a command and its output.",
        "# fingerprint is filled automatically the first time a valid sign-off is seen; STALE entries",
        "# need re-verification, then: py -3 tb21/master_check.py <slug> --restamp N,M",
        "",
    ]
    for n in sorted(CHECKS):
        sec, title, mode, _ = CHECKS[n]
        st = statuses[n]
        entry = signoff.get(n)
        if st == "PASS" and entry is None:
            continue
        if st == "FAIL" and entry is None and mode == "auto":
            continue
        key = "cci" if n == CI else f"c{n}"
        out.append(f"[{key}]  # {sec} {n if n != CI else 'CI'}: {title} [{st}]")
        for f in ctx.findings.get(n, [])[:6]:
            if f.level != "info" or mode != "auto":
                out.append(f"# {f.level}: {f.msg[:200]}")
        e = entry or {}
        out.append(f"status = {tq(str(e.get('status', '')))}")
        out.append(f"evidence = {tq(str(e.get('evidence', '')))}")
        out.append(f"fingerprint = {tq(str(e.get('fingerprint', '')))}")
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- report


def md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def write_report(path: Path, ctx: Ctx, statuses: dict[int, str], signoff: dict[int, dict], sha: str) -> None:
    counts: dict[str, int] = {}
    for st in statuses.values():
        counts[st] = counts.get(st, 0) + 1
    order = ["FAIL", "STALE", "REVIEW", "MANUAL", "SIGNED", "PASS"]
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = [
        f"# Master Ship Checklist - {ctx.slug}",
        "",
        f"Bundle sha `{sha}`, generated {now}. " + ", ".join(f"{k} {counts.get(k, 0)}" for k in order),
        "",
        "| # | Sec | Check | Mode | Status | First finding |",
        "|---|---|---|---|---|---|",
    ]
    for n in sorted(CHECKS):
        sec, title, mode, _ = CHECKS[n]
        fs = [f for f in ctx.findings.get(n, []) if f.level != "info"] or ctx.findings.get(n, [])
        first = fs[0].msg[:120] if fs else ""
        out.append(f"| {n if n != CI else 'CI'} | {sec} | {md(title)} | {mode} | **{statuses[n]}** | {md(first)} |")
    out += ["", "## Findings and sign-offs", ""]
    for n in sorted(CHECKS):
        fs = ctx.findings.get(n, [])
        so = signoff.get(n)
        if not fs and not so:
            continue
        sec, title, mode, _ = CHECKS[n]
        out.append(f"### {n if n != CI else 'CI'} - {title} [{statuses[n]}]")
        for f in fs:
            out.append(f"- {f.level}: {f.msg}")
        if so and (so.get("status") or so.get("evidence")):
            out.append(f"- sign-off ({so.get('status', '')}): {so.get('evidence', '')}")
        out.append("")
    for section, lines in ctx.appendix.items():
        out += [f"## Appendix - {section}", ""] + [f"- {ln}" for ln in lines] + [""]
    path.write_text("\n".join(out), encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- main


def build_ctx(outer: Path) -> Ctx:
    ctx = Ctx(outer=outer, slug=outer.name, inner=outer / outer.name)
    ctx.env = ctx.inner / "environment"
    ctx.instruction = read(ctx.inner / "instruction.md")
    for ln in read(outer / "rubric.txt").splitlines():
        m = re.match(r"^(.*),\s*([+-]\d+)\s*$", ln.strip())
        if m:
            ctx.rubric.append((m.group(1).strip(), int(m.group(2))))
    ctx.tests_text = "\n".join(read(p) for p in files(ctx.inner / "tests"))
    ctx.solve = read(ctx.inner / "solution" / "solve.sh")
    ctx.image = ImageMap(ctx.env) if ctx.env.is_dir() else None
    return ctx


def fingerprints(ctx: Ctx, sha: str) -> dict[str, str]:
    o = ctx.outer
    rubric = [o / "rubric.txt"] if (o / "rubric.txt").is_file() else []
    ev = files(o / "oracle-nop-evidence")
    traj = [p for p in files(o / "trajectories") if p.name not in {"config.json", "result.json"}]
    return {
        "task": sha,
        "rubric": fp(rubric, o, sha),
        "evidence": fp(ev, o, sha),
        "traj": fp(traj + rubric, o, sha),
        "delivery": fp(files(o), o),
    }


def evaluate(ctx: Ctx, signoff: dict[int, dict], fps: dict[str, str]) -> dict[int, str]:
    statuses = {}
    for n, (_, _, mode, scope) in CHECKS.items():
        fs = ctx.findings.get(n, [])
        if any(f.level == "error" for f in fs):
            statuses[n] = "FAIL"
            continue
        warned = any(f.level == "warn" for f in fs)
        if n == 30:
            needs = warned or not ctx.appendix.get("Ablation (check 30)")
        elif n == 31:
            needs = warned or not any(f.msg.startswith("cold linux/amd64") for f in fs)
        else:
            needs = mode != "auto" or warned
        if not needs:
            statuses[n] = "PASS"
            continue
        e = signoff.get(n) or {}
        st = str(e.get("status", "")).strip().lower()
        if st == "fail":
            statuses[n] = "FAIL"
        elif st in {"pass", "n/a"} and evidence_ok(str(e.get("evidence", ""))):
            statuses[n] = "SIGNED" if e.get("fingerprint") == fps[scope] else "STALE"
        else:
            statuses[n] = "REVIEW" if warned else "MANUAL"
    return statuses


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug_dir")
    ap.add_argument("--restamp", default="", help="comma-separated check numbers to re-bind after re-verification")
    args = ap.parse_args()

    outer = ship.resolve_outer(args.slug_dir)
    if not (outer / outer.name).is_dir():
        print(f"not a delivery folder (<slug>/<slug>/ missing): {outer}")
        return 2
    ctx = build_ctx(outer)
    sha = ship.bundle_sha(ctx.inner)

    static_report = static.check_task(ctx.inner, outer)
    ingest(ctx, static_report.errors + static_report.warns, map_static)
    ship_report, _ = ship.run_all(outer)
    ingest(ctx, ship_report.errors + ship_report.warns, map_ship)

    check_instruction(ctx)
    check_environment(ctx)
    touches = check_solution(ctx)
    check_tests(ctx)
    check_toml_text(ctx)
    check_rubric(ctx)
    check_trajectories(ctx)
    check_run_records(ctx, sha, touches)

    # A trajectory that merely mentions grading paths in output is fine when no agent command touched them.
    cmd_hits = {m.group(1) for f in ctx.findings.get(81, []) if f.level == "error" and (m := re.match(r"(run-0\d):", f.msg))}
    for f in ctx.findings.get(81, []):
        m = re.search(r"(run-0\d): trajectory mentions grading paths", f.msg)
        if f.level == "warn" and m and m.group(1) not in cmd_hits:
            f.level = "info"
            f.msg += " (no agent command touched them - mention is in output/prose only)"

    rep = REPORTS / ctx.slug
    rep.mkdir(parents=True, exist_ok=True)
    so_path = rep / "signoff.toml"
    signoff = load_signoff(so_path)
    fps = fingerprints(ctx, sha)
    restamp = {CI if x.strip().lower() == "ci" else int(x) for x in args.restamp.split(",") if x.strip()}
    for n, e in signoff.items():
        if n not in CHECKS:
            continue
        valid = str(e.get("status", "")).strip().lower() in {"pass", "n/a"} and evidence_ok(str(e.get("evidence", "")))
        if valid and (not e.get("fingerprint") or n in restamp):
            e["fingerprint"] = fps[CHECKS[n][3]]
    statuses = evaluate(ctx, signoff, fps)
    write_signoff(so_path, ctx, signoff, statuses, sha)
    write_report(rep / "MASTER_REPORT.md", ctx, statuses, signoff, sha)

    counts: dict[str, list[int]] = {}
    for n, st in statuses.items():
        counts.setdefault(st, []).append(n)
    label = lambda n: "CI" if n == CI else str(n)  # noqa: E731
    print(f"== master_check: {ctx.slug} (bundle {sha}) ==")
    for st in ("FAIL", "STALE", "REVIEW", "MANUAL"):
        for n in sorted(counts.get(st, [])):
            fs = [f for f in ctx.findings.get(n, []) if f.level in {"error", "warn"}]
            extra = f" - {fs[0].msg[:150]}" + (f" (+{len(fs) - 1} more)" if len(fs) > 1 else "") if fs else ""
            print(f"{st:<6} [{label(n)}] {CHECKS[n][1]}{extra}")
    summary = ", ".join(f"{k} {len(counts.get(k, []))}" for k in ("FAIL", "STALE", "REVIEW", "MANUAL", "SIGNED", "PASS"))
    print(f"-- {summary}")
    print(f"report:   {(rep / 'MASTER_REPORT.md').relative_to(ROOT)}")
    print(f"sign-off: {so_path.relative_to(ROOT)}")
    ready = all(st in {"PASS", "SIGNED"} for st in statuses.values())
    print("READY: every check PASS/SIGNED" if ready else "NOT READY: fix FAIL items; answer REVIEW/MANUAL/STALE in signoff.toml with evidence")
    return 0 if ready else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
