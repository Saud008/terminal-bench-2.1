#!/usr/bin/env python3
"""Write platform submission explanations to submission-explanations/<slug>.md.

  python3 scripts/write_submission_explanations.py --slug my-task --draft
  python3 scripts/write_submission_explanations.py --slug my-task --text-file explanations.txt

Draft mode inspects the real task tree and writes task-specific paragraphs (edit before upload).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from submission_explanations_paths import (  # noqa: E402
    EXPLANATIONS_DIR,
    REQUIRED_SECTIONS,
    explanations_path,
    parse_sections,
    sentence_count,
    task_dir_for_slug,
)


def _read(path: Path, limit: int = 8000) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def _list_docs(task_dir: Path) -> list[str]:
    docs = task_dir / "environment"
    found: list[str] = []
    for base in (docs / "docs", docs):
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.md"))[:12]:
            rel = p.relative_to(task_dir / "environment")
            found.append(f"/app/{rel.as_posix()}")
    return found[:6]


def _count_py_tests(task_dir: Path) -> int:
    tp = task_dir / "tests" / "test_outputs.py"
    if not tp.is_file():
        return 0
    return len(re.findall(r"^\s*def test_", tp.read_text(encoding="utf-8", errors="replace"), re.M))


def _primary_language(task_dir: Path) -> str:
    toml = _read(task_dir / "task.toml")
    m = re.search(r'languages\s*=\s*\[([^\]]+)\]', toml)
    if m:
        langs = re.findall(r'"([^"]+)"', m.group(1))
        if langs:
            return langs[0]
    return "unknown"


def _src_modules(task_dir: Path) -> list[str]:
    env = task_dir / "environment"
    for sub in ("src", "app/src", "cmd", "internal"):
        d = env / sub
        if d.is_dir():
            return sorted(p.name for p in d.iterdir() if p.suffix in (".go", ".rs", ".cpp", ".c", ".ts", ".js", ".py"))[:8]
    return []


def _has_tb3(task_dir: Path) -> bool:
    return "TB3_" in _read(task_dir / "instruction.md") or "TB3_" in _read(task_dir / "tests" / "test_outputs.py")


def _has_staging(task_dir: Path) -> bool:
    blob = _read(task_dir / "instruction.md") + _read(task_dir / "tests" / "test_outputs.py")
    return "snapshot" in blob.lower() or "staging" in blob.lower()


def _oracle_files(task_dir: Path) -> list[str]:
    sol = task_dir / "solution"
    for sub in ("files", "patches"):
        d = sol / sub
        if d.is_dir():
            return sorted(p.name for p in d.iterdir() if p.is_file())[:10]
    return []


def _is_milestone_task(task_dir: Path) -> bool:
    return (task_dir / "steps" / "milestone_1").is_dir()


def _milestone_count(task_dir: Path) -> int:
    toml = _read(task_dir / "task.toml")
    m = re.search(r"number_of_milestones\s*=\s*(\d+)", toml)
    if m:
        return int(m.group(1))
    n = 0
    for p in sorted(task_dir.glob("steps/milestone_*")):
        if p.is_dir():
            n += 1
    return n or 1


def _cli_binary(task_dir: Path) -> str:
    cmd = task_dir / "environment" / "cmd"
    if cmd.is_dir():
        for d in sorted(cmd.iterdir()):
            if d.is_dir():
                return d.name
    return "cli"


def _doc_basenames(task_dir: Path) -> list[str]:
    docs = task_dir / "environment" / "docs"
    if not docs.is_dir():
        return []
    return [p.name for p in sorted(docs.glob("*.md"))[:8]]


def _milestone_test_counts(task_dir: Path) -> list[int]:
    counts: list[int] = []
    for p in sorted(task_dir.glob("steps/milestone_*/tests/test_m*.py")):
        text = p.read_text(encoding="utf-8", errors="replace")
        counts.append(len(re.findall(r"^\s*def test_", text, re.M)))
    return counts


def _internal_packages(task_dir: Path) -> list[str]:
    internal = task_dir / "environment" / "internal"
    if not internal.is_dir():
        return _src_modules(task_dir)
    return sorted(d.name for d in internal.iterdir() if d.is_dir())[:8]


def _milestone_draft_paragraphs(task_dir: Path, slug: str) -> dict[str, str]:
    """Milestone Go/CLI tasks — drafts emphasize why-hard vs how-verified separation."""
    lang = _primary_language(task_dir)
    n_ms = _milestone_count(task_dir)
    binary = _cli_binary(task_dir)
    docs = _doc_basenames(task_dir)
    packages = _internal_packages(task_dir)
    test_counts = _milestone_test_counts(task_dir)
    diff = _read(task_dir / "task.toml")
    difficulty = "hard" if 'difficulty = "hard"' in diff else "medium"

    doc_hint = ", ".join(docs[:5]) if docs else "several docs under /app/docs/"
    pkg_hint = ", ".join(packages[:6]) if packages else "multiple internal packages"
    test_hint = (
        ", ".join(f"M{i + 1} has {c} tests" for i, c in enumerate(test_counts))
        if test_counts
        else "each milestone has independent pytest cases"
    )

    m1_blob = _read(task_dir / "steps" / "milestone_1" / "instruction.md")
    behaviors: list[str] = []
    for token in (
        "checksum",
        "pending",
        "tx_commit",
        "snapshot",
        "manifest",
        "publish",
        "barrier",
        "compaction",
        "epoch",
        "writebatch",
        "offset",
    ):
        if token in m1_blob.lower() or any(token in d.lower() for d in docs):
            behaviors.append(token)
    behavior_hint = ", ".join(behaviors[:5]) if behaviors else "replay, manifest, and export contracts"

    difficulty_p = (
        f"This {n_ms}-milestone {lang} task is marked {difficulty} because agents must wire a {binary} CLI "
        f"where {behavior_hint} interact across {pkg_hint} and the docs ({doc_hint}). "
        f"Each milestone adds constraints the broken baseline violates on purpose, so patching one package "
        f"often leaves later replay or publish stages inconsistent with the spec. "
        f"Humans miss doc-only rules (barrier ordering, manifest-only export, checksum cursors) as often as "
        f"models stop after the first compiling fix. "
        f"Partial progress on milestone one still fails overlay or tamper suites, and milestone three "
        f"breaks if publish re-reads inputs instead of the on-disk manifest."
    )

    solution_p = (
        f"The oracle applies golden patches per milestone into /app/internal, rebuilds {binary} with go build, "
        f"and keeps earlier milestone behavior intact while layering new packages. "
        f"The core insight is to treat replay as the only writer of live key state, keep barrier/snapshot "
        f"semantics in the packages the docs name, and restrict publish to manifest bytes plus schema fields. "
        f"Milestone ordering matters: header/bucket parsing and store materialization must be correct before "
        f"truncation or tx-id reset logic runs. "
        f"Manifest assembly must be stable before export digest rules execute, otherwise later milestones pass "
        f"compile but still emit reports that disagree with the reference harness."
    )

    verification_p = (
        f"Each milestone test.sh rebuilds {binary}, then pytest drives documented subcommands via subprocess "
        f"against bundled suites under /app/fixtures/suites/. "
        f"Shared harness and reference modules under /opt/verifier-shared recompute manifests and reports "
        f"from fixture bytes without importing /app/internal, so hard-coded JSON cannot pass. "
        f"{test_hint.capitalize()}; hidden verifier-only suites exercise traps absent from the public bundle. "
        f"Checksum tamper, pending-overlay, and manifest-only publish cases catch fixes that work on the "
        f"default tree but violate the contract on mutated or hidden inputs."
    )

    return {
        "Difficulty Explanation": difficulty_p.strip(),
        "Solution Explanation": solution_p.strip(),
        "Verification Explanation": verification_p.strip(),
    }


def draft_paragraphs(task_dir: Path, slug: str) -> dict[str, str]:
    """Task-specific draft — agent/user must still edit to own voice."""
    if _is_milestone_task(task_dir):
        return _milestone_draft_paragraphs(task_dir, slug)
    lang = _primary_language(task_dir)
    docs = _list_docs(task_dir)
    modules = _src_modules(task_dir)
    n_tests = _count_py_tests(task_dir)
    oracle_files = _oracle_files(task_dir)
    staging = _has_staging(task_dir)
    tb3 = _has_tb3(task_dir)
    diff = _read(task_dir / "task.toml")
    difficulty = "hard" if 'difficulty = "hard"' in diff else "medium"

    doc_hint = ", ".join(docs[:3]) if docs else "/app/docs/"
    mod_hint = ", ".join(modules[:5]) if modules else "several modules under /app"
    oracle_hint = ", ".join(oracle_files[:5]) if oracle_files else "broken sources under /app"

    difficulty_p = (
        f"This task is marked {difficulty} because the agent must repair a {lang} pipeline where ingest, "
        f"staging, and export disagree unless several layers are fixed together. "
        f"The contract is split across {doc_hint}, so fixing only parsing or only export math still fails hidden checks. "
    )
    if staging:
        difficulty_p += (
            "Export must consume the on-disk staging snapshot and manifest digest, not re-walk raw inputs, "
            "which is easy to miss when bundled fixtures look fine after a one-file patch. "
        )
    else:
        difficulty_p += (
            "Behavior spans multiple source files ({mod_hint}), and a plausible partial fix often passes "
            "some bundled runs while cross-run or replay tests still fail. "
        ).format(mod_hint=mod_hint)
    if tb3:
        difficulty_p += (
            "TB3_* environment overrides point ingest at verifier-only directories, so path handling and "
            "discovery rules must match the docs, not just the default bundle. "
        )
    difficulty_p += (
        f"Frontier models tend to stop after the first obvious bug in one module even though {n_tests} behavioral "
        "tests require the full contract to line up."
    )

    solution_p = (
        f"The oracle copies corrected sources ({oracle_hint}) into /app, rebuilds the project, and runs the "
        "documented CLI end-to-end. "
        "The main insight is to keep ingest responsible for merge semantics and snapshot bytes while export "
        "derives gaps, fingerprints, and summaries only from that staged artifact. "
    )
    if staging:
        solution_p += (
            "Manifest SHA-256 must match the snapshot file on disk so export validation and pytest staging "
            "assertions agree. "
        )
    solution_p += (
        "Exit-code precedence between skipped shards versus timeline gaps must follow the instruction and "
        "cli-surface docs, not ad-hoc ordering in emit. "
        "Re-running correlate on unchanged inputs should be idempotent because staging and outputs are "
        "written through the same code paths agents are expected to fix."
    )

    verification_p = (
        f"Pytest ({n_tests} cases) rebuilds the binary in test.sh, then drives the CLI via subprocess with "
        "fresh output paths per test. "
        "An independent reference implementation in the test module recomputes expected JSON from the same "
        "fixtures and schemas cited in instruction.md, so hard-coded report files cannot pass. "
    )
    if staging:
        verification_p += (
            "Dedicated tests assert the staging snapshot and manifest exist with the ingest contract before "
            "export fields are checked. "
        )
    if tb3:
        verification_p += (
            "Hidden verifier fixtures under TB3 overrides exercise discovery and export behavior that bundled "
            "trees alone do not cover. "
        )
    verification_p += (
        "Mutated inputs and byte-level comparisons on reports catch fixes that only work on the default "
        "bundle while leaving export or persistence layers broken."
    )

    return {
        "Difficulty Explanation": difficulty_p.strip(),
        "Solution Explanation": solution_p.strip(),
        "Verification Explanation": verification_p.strip(),
    }


def format_file(slug: str, sections: dict[str, str]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Submission explanations — {slug}",
        "",
        f"**Task folder:** tasks/{slug}/",
        "**Platform form only** — not in upload zip.",
        f"**Updated:** {ts}",
        "",
        "> Edit in your own words before pasting on the platform form.",
        "> Length cap: 4–6 sentences, ≤6 prose lines, ~≤120 words per section (Difficulty · Solution · Verification).",
        "> Prose: plain Indian English — avoid ; : — digits and path dumps; spell counts in words.",
        "> Agent draft — rewrite and trim; never paste verbatim (Terminus zero-tolerance policy).",
        "",
    ]
    for title in REQUIRED_SECTIONS:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(sections.get(title, "").strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_text_file(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    missing = [t for t in REQUIRED_SECTIONS if t not in sections or not sections[t].strip()]
    if missing:
        raise ValueError(f"text-file missing sections: {', '.join(missing)}")
    return sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--draft", action="store_true", help="Generate from task tree inspection")
    parser.add_argument("--text-file", type=Path, help="Parse sections from an existing draft file")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    slug = args.slug.strip().strip("/")
    task_dir = task_dir_for_slug(slug)
    if not task_dir and not args.force:
        print(f"ERROR: no tasks/{slug}/ or pending/{slug}/", file=sys.stderr)
        return 1

    if args.text_file:
        sections = load_text_file(args.text_file)
    elif args.draft:
        if not task_dir:
            print("ERROR: --draft needs an existing task folder", file=sys.stderr)
            return 1
        sections = draft_paragraphs(task_dir, slug)
    else:
        parser.error("Use --draft or --text-file")

    EXPLANATIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = explanations_path(slug)
    out.write_text(format_file(slug, sections), encoding="utf-8")

    print(f"Wrote {out.relative_to(REPO_ROOT)}")
    for title in REQUIRED_SECTIONS:
        n = sentence_count(sections[title])
        print(f"  {title}: ~{n} sentences")
    print("Edit for your voice, then: python3 scripts/submission_explanations_gate.py --check --slug", slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
