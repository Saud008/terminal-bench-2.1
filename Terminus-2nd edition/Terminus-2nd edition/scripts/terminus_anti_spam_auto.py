#!/usr/bin/env python3
"""Automated anti-spam / templated checks for Terminus workflow phases.

Runs the multi-signal pipeline (thresholds locked in anti_spam_pipeline.py):
  Ideas: IDEA_VERDICT_FAIL = 0.10 (block if weighted > 0.10); auto @CREATE when weighted == 0.0
  Pack/post-create: VERDICT_FAIL = 0.85 · VERDICT_WARN = 0.65

Phases:
  ideas        — screen proposed titles before build (newidea / generate-ideas)
  post-create  — full gate after tasks/<name>/ or pending/<name>/ exists
  pack         — same as pack_zip.sh --pack-gate (optional wrapper)

Examples:
  python3 scripts/terminus_anti_spam_auto.py ideas --json ideas.json
  python3 scripts/terminus_anti_spam_auto.py ideas --title "Rust WAL repair" --language rust
  python3 scripts/terminus_anti_spam_auto.py post-create --task-dir tasks/my-task
  python3 scripts/terminus_anti_spam_auto.py post-create --task-name my-task
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from anti_spam_pipeline import (
        IDEA_AUTO_CREATE_SIM,
        IDEA_VERDICT_FAIL,
        SIGNAL_WEIGHTS,
        VERDICT_FAIL,
        VERDICT_WARN,
        TaskMetadata,
        classify_unacceptable_classes,
        final_verdict,
        format_pipeline_report,
        heuristic_judge,
        idea_should_auto_create,
        idea_similarity_verdict,
        load_or_build_index,
        pipeline_to_dict,
        score_idea_text,
        slugify_title,
    )
    from terminus_anti_spam_check import (
        FAMILY_MATCHERS,
        Fingerprint,
        REPO_ROOT as CHECK_REPO,
        SPAM_SLUG_RE,
        build_all_fingerprints,
        build_all_metadata,
        check_one,
        family_label,
        format_line,
        load_all_submission_slugs,
        locate_task_dir,
        slug_token_jaccard,
    )
except ImportError:
    from scripts.anti_spam_pipeline import (  # type: ignore[no-redef]
        IDEA_AUTO_CREATE_SIM,
        IDEA_VERDICT_FAIL,
        SIGNAL_WEIGHTS,
        VERDICT_FAIL,
        VERDICT_WARN,
        TaskMetadata,
        classify_unacceptable_classes,
        final_verdict,
        format_pipeline_report,
        heuristic_judge,
        idea_should_auto_create,
        idea_similarity_verdict,
        load_or_build_index,
        pipeline_to_dict,
        score_idea_text,
        slugify_title,
    )
    from scripts.terminus_anti_spam_check import (  # type: ignore[no-redef]
        FAMILY_MATCHERS,
        Fingerprint,
        REPO_ROOT as CHECK_REPO,
        SPAM_SLUG_RE,
        build_all_fingerprints,
        build_all_metadata,
        check_one,
        family_label,
        format_line,
        load_all_submission_slugs,
        locate_task_dir,
        slug_token_jaccard,
    )

REPO_ROOT = CHECK_REPO
REPORT_DIR = REPO_ROOT / "jobs-local"
IDEAS_REPORT = REPORT_DIR / "anti-spam-ideas-last.json"
POST_CREATE_REPORT = REPORT_DIR / "anti-spam-post-create-last.json"


@dataclass
class ProposedIdea:
    title: str
    language: str = ""
    milestone: bool = False
    summary: str = ""
    behaviors: list[str] = field(default_factory=list)
    slug: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            self.slug = slugify_title(self.title)

    def blob(self) -> str:
        parts = [self.title, self.language, self.summary, " ".join(self.behaviors)]
        return "\n".join(p for p in parts if p)

    def similarity_blob(self) -> str:
        """Domain/language/summary only — title excluded from intake similarity."""
        parts = [self.language, self.summary, " ".join(self.behaviors)]
        return "\n".join(p for p in parts if p)


@dataclass
class IdeaScreenResult:
    title: str
    slug: str
    status: str
    nearest: str | None = None
    weighted_score: float = 0.0
    semantic: float = 0.0
    families: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    auto_create: bool = False
    unacceptable_classes: list[str] = field(default_factory=list)

    def audit_line(self) -> str:
        neighbor = self.nearest or "none"
        auto = " AUTO_CREATE" if self.auto_create else ""
        if self.status == "PASS":
            return (
                f"Anti-spam/templated: PASS — {self.title} (slug {self.slug}) "
                f"— nearest {neighbor} (sim {self.weighted_score}) — risk Low{auto}"
            )
        if self.status == "WARNING":
            warn = "; ".join(self.warnings[:2]) or "moderate similarity"
            return (
                f"Anti-spam/templated: WARN — {self.title} (slug {self.slug}) "
                f"— nearest {neighbor} (sim {self.weighted_score}) — {warn}"
            )
        block = "; ".join(self.blockers[:2])
        return (
            f"Anti-spam/templated: FAIL — {self.title} (slug {self.slug}) "
            f"— nearest {neighbor} (sim {self.weighted_score}) — {block}"
        )


def collect_known_slugs() -> set[str]:
    known: set[str] = set()
    roots = [
        REPO_ROOT / "tasks",
        REPO_ROOT / "pending",
        REPO_ROOT / "tasks" / "_accepted-tasks",
        REPO_ROOT / "tasks" / "tasksss",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.iterdir():
            if p.is_dir() and (p / "task.toml").is_file():
                known.add(p.name)
    zdir = REPO_ROOT / "tasksubmit"
    if zdir.is_dir():
        known.update(z.stem for z in zdir.glob("*.zip"))
    known |= load_all_submission_slugs(REPO_ROOT / "scripts" / "platform_submissions.txt")
    return known


def _proposed_families(slug: str, language: str, text: str) -> list[str]:
    langs = tuple(sorted({language.lower()})) if language else ()
    fp = Fingerprint(
        slug=slug,
        langs=langs,
        has_go=language.lower() == "go",
        has_cargo=language.lower() == "rust",
        has_package_json=language.lower() in ("javascript", "typescript", "node"),
    )
    blob = f"{slug} {text.lower()}"
    return [fid for fid, _label, matcher in FAMILY_MATCHERS if matcher(blob, fp)]


def _family_counts(all_fps: dict[str, Fingerprint]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fp in all_fps.values():
        for fam in fp.families:
            counts[fam] = counts.get(fam, 0) + 1
    return counts


def screen_idea(
    idea: ProposedIdea,
    *,
    known_slugs: set[str],
    all_fps: dict[str, Fingerprint],
    all_meta: dict[str, TaskMetadata],
    index: dict,
    family_saturation: int = 3,
) -> IdeaScreenResult:
    result = IdeaScreenResult(title=idea.title, slug=idea.slug, status="PASS")
    text = idea.similarity_blob()

    if SPAM_SLUG_RE.search(idea.slug):
        result.blockers.append(f"spam slug pattern: {idea.slug}")

    if idea.slug in known_slugs:
        result.blockers.append(f"slug already exists: {idea.slug}")

    for existing in known_slugs:
        if existing == idea.slug:
            continue
        if slug_token_jaccard(idea.slug, existing) >= 0.72:
            result.blockers.append(f"near-duplicate slug vs {existing}")
            break

    families = _proposed_families(idea.slug, idea.language, text)
    result.families = families
    fcounts = _family_counts(all_fps)
    for fam in families:
        if fcounts.get(fam, 0) >= family_saturation:
            result.blockers.append(
                f"family saturation: {fam} ({family_label(fam)}) "
                f"has {fcounts[fam]} tasks (max {family_saturation - 1})"
            )

    signals, nearest = score_idea_text(text, idea.slug, index, all_meta)
    weighted = signals.weighted
    result.nearest = nearest
    result.weighted_score = weighted
    result.semantic = signals.semantic

    sim_status = idea_similarity_verdict(weighted)
    if sim_status == "FAIL":
        result.blockers.append(
            f"idea similarity blocked: weighted {weighted:.3f} > {IDEA_VERDICT_FAIL} "
            f"(nearest {nearest}, sem={signals.semantic})"
        )

    if result.blockers:
        result.status = "FAIL"
        result.auto_create = False
    else:
        result.status = "PASS"
        result.auto_create = idea_should_auto_create(weighted, has_blockers=False)
        if not result.auto_create and weighted > IDEA_AUTO_CREATE_SIM:
            result.warnings.append(
                f"similarity {weighted:.3f} > 0 — confirm before build or pick new domain"
            )
    shared_family = False
    if nearest and nearest in all_fps:
        shared_family = bool(set(families) & set(all_fps[nearest].families))
    result.unacceptable_classes = classify_unacceptable_classes(
        blockers=result.blockers,
        warnings=result.warnings,
        similarity=weighted,
        shared_family_neighbor=shared_family,
        similarity_fail=IDEA_VERDICT_FAIL,
    )
    return result


def load_ideas_json(path: Path) -> list[ProposedIdea]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("ideas", data) if isinstance(data, dict) else data
    ideas: list[ProposedIdea] = []
    for item in raw:
        if isinstance(item, str):
            ideas.append(ProposedIdea(title=item))
            continue
        ideas.append(
            ProposedIdea(
                title=item.get("title") or item.get("task_title") or "untitled",
                language=item.get("language") or item.get("primary_language") or "",
                milestone=bool(item.get("milestone", False)),
                summary=item.get("summary") or item.get("description") or "",
                behaviors=list(item.get("behaviors") or item.get("bugs") or []),
                slug=item.get("slug") or "",
            )
        )
    return ideas


def run_ideas_phase(
    ideas: list[ProposedIdea],
    *,
    rebuild_index: bool = False,
    markdown_table: bool = False,
) -> tuple[int, list[IdeaScreenResult]]:
    all_fps = build_all_fingerprints()
    all_meta = build_all_metadata(rebuild_index=rebuild_index)
    index = load_or_build_index(all_meta, rebuild=rebuild_index)
    known = collect_known_slugs()

    results = [
        screen_idea(idea, known_slugs=known, all_fps=all_fps, all_meta=all_meta, index=index)
        for idea in ideas
    ]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "ideas",
        "thresholds": {
            "idea_fail_gt": IDEA_VERDICT_FAIL,
            "idea_auto_create_sim": IDEA_AUTO_CREATE_SIM,
            "pack_fail": VERDICT_FAIL,
            "pack_warn": VERDICT_WARN,
            "weights": SIGNAL_WEIGHTS,
        },
        "results": [asdict(r) for r in results],
        "audit_lines": [r.audit_line() for r in results],
        "auto_create_slugs": [r.slug for r in results if r.auto_create],
    }
    IDEAS_REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if markdown_table:
        print("### Anti-spam idea screen\n")
        print("| # | Title | Slug | Status | Nearest | Sim |")
        print("|---|-------|------|--------|---------|-----|")
        for i, r in enumerate(results, 1):
            print(
                f"| {i} | {r.title} | {r.slug} | {r.status} | {r.nearest or '—'} | {r.weighted_score} |"
            )
        print("\n### Audit lines\n")
        for line in payload["audit_lines"]:
            print(f"- {line}")
    else:
        for r in results:
            print(r.audit_line())

    fail = sum(1 for r in results if r.status == "FAIL")
    warn = sum(1 for r in results if r.status == "WARNING")
    print(
        f"--- ideas screen: pass={len(results) - fail - warn} warn={warn} fail={fail} "
        f"(report: {IDEAS_REPORT}) ---",
        file=sys.stderr if fail else sys.stdout,
    )
    return (1 if fail else 0), results


def run_post_create_phase(
    slug: str,
    *,
    rebuild_index: bool = False,
    use_llm: bool = False,
    strict: bool = False,
) -> tuple[int, dict]:
    task_dir = locate_task_dir(slug)
    if task_dir is None:
        print(f"ERROR: no task dir for slug {slug}", file=sys.stderr)
        return 1, {}

    all_fps = build_all_fingerprints()
    platform = load_all_submission_slugs(REPO_ROOT / "scripts" / "platform_submissions.txt")
    all_meta = build_all_metadata(rebuild_index=rebuild_index)

    result = check_one(
        slug,
        all_fps,
        platform,
        strict=strict,
        all_meta=all_meta,
        rebuild_index=rebuild_index,
        use_llm=use_llm,
    )
    line = format_line(result, include_pipeline=True)
    print(line)

    payload = asdict(result)
    if result.pipeline is not None:
        payload["pipeline_detail"] = pipeline_to_dict(result.pipeline)
        print(f"  {format_pipeline_report(result.pipeline)}")

    if result.blockers:
        for b in result.blockers:
            print(f"  blocker: {b}", file=sys.stderr)
    if result.warnings:
        for w in result.warnings:
            print(f"  warn: {w}")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "phase": "post-create",
        "slug": slug,
        "task_dir": str(task_dir),
        "thresholds": {"fail": VERDICT_FAIL, "warn": VERDICT_WARN, "weights": SIGNAL_WEIGHTS},
        "audit_line": line,
        "result": payload,
    }
    POST_CREATE_REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"--- post-create report: {POST_CREATE_REPORT} ---")

    if result.status == "FAIL":
        return 1, out
    return 0, out


def run_pack_phase(slug: str, *, strict_repo: bool = False) -> int:
    """Post-create check then full pack gate (single entry for pack_zip.sh)."""
    from terminus_anti_spam_check import run_pack_gate, write_report

    code_create, _ = run_post_create_phase(slug)
    if code_create != 0:
        return code_create

    all_fps = build_all_fingerprints()
    platform = load_all_submission_slugs(REPO_ROOT / "scripts" / "platform_submissions.txt")
    all_meta = build_all_metadata()
    code, lines = run_pack_gate(
        slug,
        all_fps,
        platform,
        strict_repo=strict_repo,
        all_meta=all_meta,
        include_pipeline=True,
    )
    for line in lines:
        print(line)
    write_report(lines)
    return code if code != 0 else code_create


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="phase", required=True)

    p_ideas = sub.add_parser("ideas", help="Screen proposed ideas before create")
    p_ideas.add_argument("--json", type=str, help="JSON file: {ideas:[{title,language,...}]}")
    p_ideas.add_argument("--title", action="append", default=[], help="Proposed title (repeatable)")
    p_ideas.add_argument("--language", default="", help="With single --title")
    p_ideas.add_argument("--summary", default="", help="With single --title")
    p_ideas.add_argument("--markdown-table", action="store_true", help="newidea closing table")
    p_ideas.add_argument("--rebuild-index", action="store_true")

    p_create = sub.add_parser("post-create", help="After task folder exists")
    p_create.add_argument("--task-dir", type=str, help="Path to task folder")
    p_create.add_argument("--task-name", type=str, help="Task slug")
    p_create.add_argument("--rebuild-index", action="store_true")
    p_create.add_argument("--llm-judge", action="store_true")
    p_create.add_argument("--strict", action="store_true")

    p_pack = sub.add_parser("pack", help="Pack-gate wrapper (same thresholds)")
    p_pack.add_argument("--task-name", required=True)
    p_pack.add_argument("--strict-repo", action="store_true")

    args = parser.parse_args()

    if args.phase == "ideas":
        ideas: list[ProposedIdea] = []
        if args.json:
            ideas.extend(load_ideas_json(Path(args.json)))
        for title in args.title:
            ideas.append(
                ProposedIdea(
                    title=title,
                    language=args.language if len(args.title) == 1 else "",
                    summary=args.summary if len(args.title) == 1 else "",
                )
            )
        if not ideas:
            parser.error("ideas phase needs --json or at least one --title")
        code, _ = run_ideas_phase(
            ideas,
            rebuild_index=args.rebuild_index,
            markdown_table=args.markdown_table,
        )
        return code

    if args.phase == "post-create":
        slug = args.task_name
        if args.task_dir:
            slug = Path(args.task_dir).resolve().name
        if not slug:
            parser.error("post-create needs --task-dir or --task-name")
        code, _ = run_post_create_phase(
            slug,
            rebuild_index=args.rebuild_index,
            use_llm=args.llm_judge,
            strict=args.strict,
        )
        return code

    if args.phase == "pack":
        return run_pack_phase(args.task_name, strict_repo=args.strict_repo)

    return 0


if __name__ == "__main__":
    sys.exit(main())
