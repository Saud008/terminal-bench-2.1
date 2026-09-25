#!/usr/bin/env python3
"""Terminus beforeSubmitPrompt hook — analyze pasted summary → best prompts/ file."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOK_SCRIPTS = _REPO_ROOT / "scripts"
if _HOOK_SCRIPTS.is_dir():
    sys.path.insert(0, str(_HOOK_SCRIPTS))

try:
    from anti_spam_hook_runner import (
        handle_prompt_submit,
        write_ideas_draft_template,
    )
except ImportError:
    handle_prompt_submit = None  # type: ignore[misc, assignment]
    write_ideas_draft_template = None  # type: ignore[misc, assignment]

try:
    from terminus_rules_engine import (
        TERMINUS_ENGINE,
        build_route_context,
        enrich_engine_from_prompt,
    )
except ImportError:
    build_route_context = None  # type: ignore[misc, assignment]
    enrich_engine_from_prompt = None  # type: ignore[misc, assignment]
    TERMINUS_ENGINE = "TERMINUS"


@dataclass
class Summary:
    difficulty: str | None = None
    status: str | None = None
    oracle_failed: bool = False
    verifier_failed: bool = False
    trivial_easy: bool = False
    not_solvable: bool = False
    zero_forever: bool = False
    agents_easy: bool = False
    has_reviewer: bool = False
    signals: list[str] = field(default_factory=list)


@dataclass
class Route:
    router: str
    case_file: str | None
    phase: str
    reason: str
    confidence: str  # high | medium | low
    engine: str = "ENGINE_7"
    summary_note: str = ""
    ask: str | None = None


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _hook_should_run(prompt: str, tagged: list[str], task: str | None) -> bool:
    """Fire hook on task path, @ hints, long paste, or lifecycle keywords."""
    if task or tagged or len(prompt) > 60:
        return True
    if _has_platform_summary(prompt):
        return True
    low = prompt.lower()
    return _any(
        [
            r"fix\s+task",
            r"\bharden\b",
            r"@trivial",
            r"\bTRIVIAL\b",
            r"\bEASY\b",
            r"trivial-fix-invoke",
            r"gen\s+ideas",
            r"generate\s+\d*\s*ideas",
            r"brainstorm",
            r"aap gen karo",
            r"@AUDIT",
            r"audit\s+tasks/",
            r"pre-?upload",
            r"pre-?zip",
            r"oracle\s+and\s+nop",
            r"pack[_ ]zip",
            r"@CREATE",
            r"@VERIFY",
            r"@ZIP",
        ],
        low,
    )


def _detect_verify_zip_phase(low: str, tagged: list[str]) -> tuple[bool, bool]:
    verify = any(
        x in tagged for x in ("verify",)
    ) or _any(
        [
            r"pre-upload",
            r"pre-zip",
            r"oracle and nop",
            r"oracle \+ nop",
            r"run oracle",
            r"run nop",
            r"@verify",
            r"verify rules",
            r"recheck from scratch",
            r"phase e\b",
            r"phase f′",
            r"phase f'",
            r"first-submit",
            r"first submit",
        ],
        low,
    )
    zip_phase = "zip" in tagged or _any(
        [
            r"pack_zip",
            r"pack zip",
            r"@zip",
            r"zip rules",
            r"ready to submit",
            r"tasksubmit/",
            r"phase g\b",
            r"phase f\b",
        ],
        low,
    )
    return verify, zip_phase


def _extract_task(text: str) -> str | None:
    m = re.search(
        r"(?:tasks|pending|tasks/_accepted-tasks)/([a-zA-Z0-9][a-zA-Z0-9_-]*)",
        text,
    )
    return m.group(1) if m else None


def _resolve_task(text: str) -> str | None:
    """Explicit path in paste, else match Unit Tests rows → tasks/*/tests."""
    task = _extract_task(text)
    if task:
        return task
    if not _has_platform_summary(text):
        return None
    try:
        from auto_easy_platform_automation import detect_slug_from_summary  # noqa: WPS433

        return detect_slug_from_summary(text)
    except Exception:
        return None


def _tagged_prompts(prompt: str, attachments: list) -> list[str]:
    found: list[str] = []
    blob = prompt
    for att in attachments or []:
        blob += " " + str(att.get("file_path") or "")
    aliases = {
        "oracleFix": [
            r"prompts/oracleFix\.md",
            r"prompts/oracle\.md",
            r"oracle-prompt\.mdc",
            r"@ORACLE PROMPT",
            r"@oracleFix",
        ],
        "reviewer": [r"prompts/reviewer\.md", r"reviewer-prompt\.mdc", r"@REVIEWER PROMPT"],
        "audit": [r"prompts/audit\.md", r"audit-prompt\.mdc", r"@AUDIT PROMPT"],
        "trivial": [r"prompts/trivial\.md", r"trivial-prompt\.mdc", r"@TRIVIAL PROMPT"],
        "medium": [r"prompts/medium\.md", r"medium-prompt\.mdc", r"@MEDIUM PROMPT"],
        "hard": [r"prompts/hard\.md", r"hard-prompt\.mdc", r"@HARD PROMPT"],
        "newidea": [
            r"prompts/newidea\.md",
            r"newTask\.md",
            r"newidea-prompt\.mdc",
            r"@NEWIDEA PROMPT",
            r"Follow newTask",
        ],
        "sphard": [
            r"prompts/sp-hard-create-revise\.md",
            r"sp-hard-create-revise",
            r"@SP HARD",
            r"sp-hard-prompt\.mdc",
        ],
        "create": [r"@CREATE", r"@CREATE RULES", r"new-task-pipeline"],
        "verify": [r"@VERIFY", r"@VERIFY RULES", r"pre-zip audit", r"pre-upload gate"],
        "zip": [r"@ZIP", r"@ZIP RULES", r"pack_zip\.sh", r"pack zip"],
    }
    for name, pats in aliases.items():
        if any(re.search(p, blob, re.I) for p in pats):
            found.append(name)
    return found


def _parse_summary(text: str) -> Summary:
    s = Summary()
    low = text.lower()

    if re.search(r"difficulty\s*[=:]\s*(medium|hard|trivial|easy)", low):
        s.difficulty = re.search(r"difficulty\s*[=:]\s*(\w+)", low).group(1)
    elif _any([r"\bmedium\b"], low) and not _any([r"\bhard\b"], low):
        s.difficulty = "medium"
    elif _any([r"\bhard\b"], low):
        s.difficulty = "hard"

    if _any([r"status\s*[=:]\s*not\s+solvable", r"\bnot\s+solvable\b", r"\bunsolvable\b"], low):
        s.not_solvable = True
        s.status = "not solvable"
    elif _any([r"status\s*[=:]\s*solvable", r"\bsolvable\b"], low):
        s.status = "solvable"
    if _any([r"\bTRIVIAL\b", r"\bEASY\b"], text):
        s.trivial_easy = True
        s.status = s.status or "TRIVIAL/EASY"

    # Oracle — strict: platform/oracle failure only (not generic "run oracle")
    s.oracle_failed = _any(
        [
            r"oracle\s+solution\s+failed",
            r"oracle\s+fail",
            r"oracle\s+reward\s*[=:]?\s*0",
            r"oracle\s+0\.0",
            r"oracle\s+0\s*%",
            r"oracle\s+0\s+passed",
            r"oracle\s+0/",
            r"\boracle:\s*0\b",
            r"g-025",
            r"g-026",
            r"g-027",
            r"missing\s+tests/test_outputs\.py",
            r"backslash.*zip",
            r"solve\.sh.*(network|download|maven|mix\s+deps|cargo\s+fetch)",
        ],
        low,
    )

    s.verifier_failed = _any(
        [
            r"verifier_did_not_run",
            r"verifier\s+did\s+not\s+run",
            r"no\s+/logs/verifier/reward",
        ],
        low,
    )

    s.zero_forever = _any(
        [
            r"0%\s*forever",
            r"0/\d+\s+forever",
            r"test[_\w]*[^\n]{0,30}0/\d+",
            r"0%-forever",
            r"never\s+pass",
            r"0%\s+on\s+test",
        ],
        low,
    ) and not re.search(r"verifier_did_not_run", low)

    s.agents_easy = _any(
        [r"5/5", r"4/5", r"passes?\s+too\s+easily", r"100%\s+pass", r"all agents pass"],
        low,
    ) or s.trivial_easy

    s.has_reviewer = _any(
        [
            r"needs_revision",
            r"reviewer feedback",
            r"reviewer:",
            r"per reviewer",
            r"line comment",
            r"human review",
            r"snorkel review",
            r"g-036",
            r"four paragraphs",
            r"lean on docs",
            r"duplicates contract",
            r"pwd guard",
            r"\bworkdir\b",
        ],
        low,
    ) or (
        bool(re.search(r"instruction\.md|test_outputs\.py|test\.sh", low))
        and _any([r"fix", r"should", r"must", r"add", r"remove", r"change"], low)
        and (
            bool(re.search(r"[-*]\s", low))
            or bool(re.search(r"^\s*\d+\.", low, re.M))
        )
    )

    if s.oracle_failed:
        s.signals.append("oracle failed")
    if s.verifier_failed:
        s.signals.append("verifier_did_not_run")
    if s.trivial_easy or s.agents_easy:
        s.signals.append("TRIVIAL/EASY or high pass rate")
    if s.not_solvable:
        s.signals.append("not solvable")
    if s.zero_forever:
        s.signals.append("0%-forever test(s)")
    if s.difficulty:
        s.signals.append(f"difficulty={s.difficulty}")
    if s.status and s.status not in s.signals:
        s.signals.append(f"status={s.status}")

    return s


def _has_platform_summary(text: str) -> bool:
    """True when pasted text looks like a platform rejection summary."""
    low = text.lower()
    hits = 0
    if _any([r"difficulty\s*:", r"\bTRIVIAL\b", r"\bEASY\b"], low):
        hits += 1
    if _any(
        [
            r"terminus-claude-opus",
            r"terminus-gpt5",
            r"agent performance",
            r"\d+/5\s+runs",
            r"\d+%\s*\(",
        ],
        low,
    ):
        hits += 1
    if _any([r"unit tests results", r"test_\w+.*\d+/\d+\s+runs"], low):
        hits += 1
    return hits >= 2


_VAGUE_TRIVIAL_FIXUP = re.compile(
    r"^(?:@(?:TRIVIAL\s+PROMPT|trivial)|@prompts/trivial\.md|"
    r"fix\s+task|harden(?:\s+it)?|make\s+it\s+harder|trivial\s+fix|easy\s+fix)[\s.!]*$",
    re.I,
)


def _is_vague_trivial_fixup(text: str) -> bool:
    stripped = text.strip()
    if _VAGUE_TRIVIAL_FIXUP.match(stripped):
        return True
    if len(stripped) < 40 and _any([r"\bfix\b", r"\bharden\b", r"\btrivial\b"], stripped.lower()):
        if not _has_platform_summary(stripped) and not _extract_task(stripped):
            return True
    return False


def _reviewer_feedback_block(task: str | None, route: Route) -> str:
    if not task or "reviewer" not in (route.router or ""):
        return ""
    slug = task
    lines = [
        "",
        "## REVIEWER FEEDBACK — mandatory gate (automatic on paste + save)",
        "",
        "Policy: compare reviewer comments vs **accepted-feedback A-001…A-010** + trivial-risk.",
        "",
        f"1. Hook saved context → `jobs-local/reviewer-feedback-context-{slug}.json`",
        "2. Read report: `jobs-local/reviewer-feedback-gate-last.json`",
        "3. **Triage table** — APPLY/PARTIAL only; **REJECT** hints that trivialize (RF6)",
        "4. If verdict **ROUTE_CASE6** → `trivial-fix-invoke.md` + Case 6 — not cosmetic reviewer fixes",
        "5. Fix valid items → **save** → hook runs `create_finish_to_zip` (sim **0.0** required)",
        "",
        "| Step | Agent |",
        "|------|-------|",
        "| 0 | Read `prompts/reviewer.md` + chosen `reviewer-feedback-N.md` |",
        "| 1 | Read gate report — map comments to A-gate failures |",
        "| 2 | Output triage: comment → APPLY/PARTIAL/REJECT + trivial? |",
        "| 3 | Edit in place — **no** instruction hints / dropped hidden tests |",
        "| 4 | Re-run probes if behavior changed |",
        "| 5 | `./scripts/create_finish_to_zip.sh " + slug + "` |",
        "",
        "**CREATE note:** audit runs automatic on save; zip only when **Anti-spam sim 0.0** + finish PASS.",
        "",
    ]
    return "\n".join(lines)


def _trivial_fixup_invoke_block(task: str | None, route: Route) -> str:
    """Inject LOCKED Case 6 invoke when TRIVIAL/EASY summary routed."""
    if route.phase != "D":
        return ""
    router = route.router or ""
    if not any(
        x in router for x in ("trivial", "easy", "trivial-fix-invoke")
    ):
        return ""
    slug = task or "<slug>"
    case = route.case_file or "prompts/trivial-case-6.md"
    td = f"tasks/{slug}" if slug != "<slug>" else "tasks/<slug>"
    lines = [
        "",
        "## TRIVIAL / EASY — MANDATORY 14 STEPS (LOCKED — DO NOT SKIP)",
        "",
        "Policy: `shared/trivial-fix-invoke-mandatory-steps.mdc` · `prompts/trivial-fix-invoke.md`",
        "",
        f"**Router:** `{route.router}` → `{case}` · **Task:** `{slug}`",
        "",
        f"**HARD GATE:** No edits to `{td}/` until Step 5 (§3 fix prompt) is in your reply.",
        "",
        "| Step | Must do now |",
        "|------|-------------|",
        "| 1 | Quote 2–3 summary facts |",
        "| 2 | `Read` `prompts/trivial-fix-invoke.md` |",
        "| 3 | `Read` trivial.md → trivial-case-6.md → sp-hard-create-revise.md |",
        "| 4 | `Read` trivial-repo-wide.md + trivial-hardening-probes.mdc |",
        "| 5 | **Write invoke §3 fix prompt** (structural plan) — **before any edit** |",
        f"| 6 | List real files under `{td}/` |",
        "| 7 | Case 6 structural edits only (staging/decoy/export/hidden/persist) |",
        f"| 8–14 | **AUTOMATIC on save** — hook runs `trivial_easy_auto_finish.sh {slug}` "
        "(probes → calibration → finish → zip). **Not** before edits on first EASY paste. |",
        "",
        "**ZERO USER COMMANDS:** User pasted platform summary only — you execute Case 6 **now**. "
        "Do not ask to harden, Case 6, or zip.",
        "",
        "**Forbidden:** Case 4/5 only · edit before step 5 · skip probes · skip finish script · decorative fields only.",
        "",
    ]
    if route.ask:
        lines.extend(["**BLOCKED — complete paste first:** " + route.ask, ""])
    return "\n".join(lines)


def _pick_trivial_case(low: str, text: str, summary: Summary) -> tuple[str, str]:
    """Return (case_file, why) — first matching row in prompts/trivial.md Step B."""
    if _any([r"audit only", r"review only", r"do not modify", r"read-?only"], low):
        return "prompts/trivial-case-audit.md", "Audit/read-only — no edits."
    if _any(
        [r"tb3", r"shallow python", r"language migration", r"autoeval", r"verifier instability"],
        low,
    ):
        return "prompts/trivial-tb3-hardening.md", "TB3 / language / verifier stability."

    easy_label = bool(re.search(r"\bEASY\b", text, re.I)) or summary.difficulty == "easy"
    both_55 = _any(
        [
            r"both.*5/5",
            r"claude.*5/5.*gpt.*5/5",
            r"gpt.*5/5.*claude.*5/5",
            r"100\.0%\s*\(\s*5/5",
        ],
        low,
    )
    either_3plus = summary.agents_easy or _any(
        [r"[34]/5", r"≥3/5", r">=3/5", r"80\.0%", r"100\.0%"], low
    )
    per_test_easy = _any(
        [r"10 passed / 10", r"9 passed / 10", r"≥6/10", r">=6/10", r"all tests.*10/10"],
        low,
    )
    case6 = _any(
        [
            r"after case 5",
            r"case 5.*still",
            r"after case 4",
            r"case 4.*still",
            r"still 5/5",
            r"one-?file patch",
            r"isolated patch",
            r"repo-?wide",
            r"repository-?wide",
            r"second trivial",
            r"2nd trivial",
            r"same slug",
            r"probes fail",
            r"decorative",
        ],
        low,
    )
    if (
        case6
        or easy_label
        or both_55
        or either_3plus
        or per_test_easy
        or re.search(r"\bTRIVIAL\b", text, re.I)
    ):
        return "prompts/trivial-case-6.md", "TRIVIAL/EASY — Case 6 structural redesign (LOCKED)."
    if _any([r"already flagged", r"do not resubmit same", r"flagged trivial"], low):
        return "prompts/trivial-case-1.md", "Already flagged trivial — reshape task."
    if _any(
        [r"both models.*≤2/5", r"both models.*2/5", r"≤2/5", r"still easy", r"deeper behavior"],
        low,
    ):
        return "prompts/trivial-case-2.md", "Still trivial but agents ≤2/5 — deepen behavior."
    return "prompts/trivial-case-6.md", "Default TRIVIAL/EASY — Case 6 (deprecated Case 4/5/harden removed)."


def _pick_medium_case(summary: Summary, low: str) -> tuple[str, str]:
    if summary.zero_forever or summary.not_solvable:
        return "prompts/medium-case-1.md", "MEDIUM + 0%-forever / not solvable — fix fairness first."
    if _any([r"solvable", r"3/5", r"~1/5", r"harden", r"too easy", r"~20%"], low) and not summary.zero_forever:
        return "prompts/medium-case-2.md", "Solvable MEDIUM — harden worst model toward ~1/5."
    return "prompts/medium-case-3.md", "MEDIUM mixed/unclear — full diagnosis."


def _pick_hard_case(summary: Summary, low: str) -> tuple[str, str]:
    if summary.zero_forever and _any(
        [
            r"claude[^\n]{0,40}0/5[^\n]{0,40}gpt[^\n]{0,20}[1-9]/5",
            r"gpt[^\n]{0,40}0/5[^\n]{0,40}claude[^\n]{0,20}[1-9]/5",
            r"some agents pass",
            r"other tests pass",
        ],
        low,
    ):
        return "prompts/hard-case-1.md", "0%-forever test(s) while others pass — unfair test/doc fix."
    if _any([r"0/5.*0/5", r"everyone fails", r"all agents 0", r"claude 0/5.*gpt 0/5"], low) and not summary.zero_forever:
        return "prompts/hard-case-2.md", "All agents 0/5 — controlled ease to ~1–2/5."
    return "prompts/hard-case-3.md", "HARD / not solvable — full fair diagnosis."


def _pick_reviewer_rf(low: str) -> tuple[str, str]:
    """Return (case_file, why) per prompts/reviewer.md Step B."""
    if _any(
        [
            r"patch /app",
            r"golden leak",
            r"drop test",
            r"bug comment",
            r"triage first",
            r"trivializ",
            r"solution hint",
        ],
        low,
    ):
        return (
            "prompts/reviewer-feedback-6.md → prompts/reviewer-feedback-4.md",
            "Trivializing risk — RF6 triage/pushback, then RF4 for valid fixes.",
        )
    if _any(
        [r"timeout", r"build_timeout", r"password", r"chpasswd", r"subcategor", r"codebase_size", r"\.dockerignore"],
        low,
    ) and not _any([r"instruction", r"test_outputs", r"behavior", r"oracle"], low):
        return "prompts/reviewer-feedback-1.md", "Metadata/CI/timeouts only — RF1 minimal fix."
    if _any([r"agent eval.*ok", r"agents ok", r"do not change difficulty", r"preserve difficulty"], low):
        return "prompts/reviewer-feedback-3.md", "Agent eval acceptable — minimal fix, preserve difficulty."
    if _any([r"run oracle", r"rerun", r"quality 11", r"static check", r"re-?verify"], low):
        return "prompts/reviewer-feedback-2.md", "Primary ask is re-verify oracle/NOP/quality."
    if _any([r"difficulty recheck", r"rubric", r"behavior.test", r"full checklist"], low):
        return "prompts/reviewer-feedback-5.md", "Broad checklist + difficulty recheck — RF5."
    return "prompts/reviewer-feedback-4.md", "Mixed line comments — RF4 default triage workflow."


def route(prompt: str, attachments: list | None = None) -> Route:
    text = prompt
    low = text.lower()
    tagged = _tagged_prompts(prompt, attachments or [])
    if re.search(r"Follow reviewer\.md", prompt, re.I):
        tagged = list(dict.fromkeys(tagged + ["reviewer"]))
    if re.search(r"Follow newTask\.md", prompt, re.I):
        tagged = list(dict.fromkeys(tagged + ["newidea"]))
    summary = _parse_summary(text)
    task = _resolve_task(text)

    # User explicitly @ oracle — only then without summary signals
    oracle_tagged = "oracleFix" in tagged

    # --- 1. Oracle issues ONLY (not all problems) ---
    if summary.oracle_failed or oracle_tagged:
        return Route(
            router="prompts/oracleFix.md",
            case_file=None,
            phase="D (oracle)",
            reason="Summary shows **oracle/zip offline failure** — use oracleFix, not trivial/medium/hard routers.",
            confidence="high" if summary.oracle_failed else "medium",
            summary_note=_summary_line(summary),
        )

    # --- 2. Reviewer line comments (not platform label alone) ---
    if summary.has_reviewer:
        rf, rf_why = _pick_reviewer_rf(low)
        return Route(
            router="prompts/reviewer.md",
            case_file=rf,
            phase="D′",
            reason=f"Reviewer feedback → **{rf}**. {rf_why}",
            confidence="high",
            summary_note=_summary_line(summary),
        )

    # --- 3a. Idea intake follow-up (before audit — "audit JSON" in idea ≠ audit phase) ---
    if (
        _idea_intake_complete(text, tagged)
        and not task
        and not summary.oracle_failed
        and not summary.has_reviewer
        and not summary.trivial_easy
        and not summary.agents_easy
        and summary.difficulty not in ("medium", "hard")
        and not summary.zero_forever
        and not summary.not_solvable
    ):
        return Route(
            router="prompts/newidea.md",
            case_file=None,
            phase="A (similarity)",
            reason=(
                "**ASK-FIRST done** — corpus scan + similarity only. "
                "**Do not** invent ideas or start @CREATE unless user says build + PASS."
            ),
            confidence="high",
            summary_note=_summary_line(summary),
        )

    # --- 3. Post-create audit ---
    audit_intent = (
        "audit" in tagged
        or _any(
            [
                r"audit\s+tasks/",
                r"audit\s+the\s+task",
                r"post-?creat",
                r"read-?only review",
                r"@AUDIT",
            ],
            low,
        )
    )
    if audit_intent and not _idea_intake_complete(text, tagged):
        return Route(
            router="prompts/audit.md",
            case_file=None,
            phase="C",
            reason="Post-create **read-only audit**.",
            confidence="high" if "audit" in tagged else "medium",
            summary_note=_summary_line(summary),
        )

    # --- 3b. Verify (E) / Zip (F) — explicit user intent ---
    verify_kw, zip_kw = _detect_verify_zip_phase(low, tagged)
    if zip_kw and not verify_kw:
        return Route(
            router="(Phase G — zip; policy in ENGINE_6; run ./scripts/pack_zip.sh)",
            case_file=None,
            phase="G",
            reason="**Zip / upload** — Phase F′ first-submit gate PASS required (never-submitted tasks); then pack_zip after oracle 1 + NOP 0.",
            confidence="high",
            summary_note=_summary_line(summary),
        )
    if verify_kw:
        return Route(
            router="(Phase E — verify; policy in ENGINE_5; oracle + NOP + F′ for first upload)",
            case_file=None,
            phase="E",
            reason="**Pre-upload verify** — oracle 1.0, NOP 0.0; **Phase F′** probe table for first upload; static preflight via `scripts/terminus_preflight.py`.",
            confidence="high",
            summary_note=_summary_line(summary),
        )

    # --- 4. SP HARD — create / revise (Claude-primary) ---
    sphard_tagged = "sphard" in tagged
    sp_create = _any([r"\bCREATE\s+tasks/", r"new\s+hard\s+task", r"sp\s+hard\s+create"], low)
    claude_zero_oracle_ok = _any(
        [
            r"terminus-claude[^\n]{0,50}0\.0%",
            r"claude[^\n]{0,40}0/5",
            r"claude[^\n]{0,40}0\.0%\s*\(0/",
        ],
        low,
    ) and _any([r"oracle[^\n]{0,40}100", r"oracle:\s*100"], low) and not summary.oracle_failed
    if sphard_tagged or sp_create:
        phase = "B (create)" if sp_create or _any([r"\bCREATE\b"], low) else "D (SP revise)"
        case = "prompts/trivial-case-6.md" if (summary.trivial_easy or summary.agents_easy) else None
        extra = " + trivial-repo-wide.md" if case else ""
        return Route(
            router="prompts/sp-hard-create-revise.md",
            case_file=case,
            phase=phase,
            reason=f"**SP hard** — Claude Opus 4.8 primary; §1b timeout-via-scope.{extra}",
            confidence="high",
            summary_note=_summary_line(summary),
        )
    if claude_zero_oracle_ok and not summary.trivial_easy and not summary.agents_easy:
        return Route(
            router="prompts/sp-hard-create-revise.md",
            case_file=None,
            phase="D (SP quality-only)",
            reason="Claude **0%** + oracle **OK** — SP quality-only; **do not weaken** for Claude.",
            confidence="medium",
            summary_note=_summary_line(summary),
        )

    # --- 5. Ideas ---
    if (
        _any(
            [
                r"new\s+idea",
                r"gen\s+ideas",
                r"generate\s+\d*\s*ideas",
                r"brainstorm",
                r"aap gen karo",
                r"@IDEAS",
            ],
            low,
        )
        or "newidea" in tagged
    ):
        if _idea_intake_complete(text, tagged):
            return Route(
                router="prompts/newidea.md",
                case_file=None,
                phase="A (similarity)",
                reason=(
                    "**ASK-FIRST done** — corpus scan + similarity only. "
                    "**Do not** invent ideas or start @CREATE unless user says build + PASS."
                ),
                confidence="high",
                summary_note=_summary_line(summary),
            )
        return Route(
            router="prompts/newidea.md",
            case_file=None,
            phase="A",
            reason=(
                "**ASK FIRST** — get language, domain, and user's idea. "
                "**No** batch generation or tasks/ build on this turn."
            ),
            confidence="high",
            summary_note=_summary_line(summary),
            ask=(
                "Reply with: (1) primary language (2) domain (3) your task idea in 1–3 sentences. "
                "I will not generate idea lists — only similarity check after you answer."
            ),
        )

    # --- 6. Verifier harness (NO oracle failure in summary) ---
    if summary.verifier_failed:
        return Route(
            router="prompts/hard-case-3.md",
            case_file=None,
            phase="D (verifier harness)",
            reason="**Verifier did not run** — fix test.sh/Dockerfile/bootstrap (runtime-verifier). **Not** oracleFix unless oracle also failed.",
            confidence="high",
            summary_note=_summary_line(summary),
        )

    # --- 7. TRIVIAL / EASY (agents pass too easily) ---
    if summary.trivial_easy or (summary.agents_easy and not summary.zero_forever and not summary.not_solvable):
        if _is_vague_trivial_fixup(text) or (not task and not _has_platform_summary(text)):
            return Route(
                router="prompts/trivial-fix-invoke.md",
                case_file="prompts/trivial-case-6.md",
                phase="D",
                reason="Vague TRIVIAL/EASY request — need slug + platform summary (`trivial-fix-invoke.md` §1).",
                confidence="high",
                ask=(
                    "Paste `tasks/<slug>/` + full platform summary (Difficulty, Status, Agent Performance, "
                    "every Unit Tests row) using `prompts/trivial-fix-invoke.md` Section 1. "
                    "Do not say only 'fix task' or '@trivial'."
                ),
            )
        if task and not _has_platform_summary(text):
            return Route(
                router="prompts/trivial-fix-invoke.md",
                case_file="prompts/trivial-case-6.md",
                phase="D",
                reason=f"Task `{task}` + TRIVIAL hint but incomplete platform summary.",
                confidence="medium",
                ask=(
                    f"Paste complete platform summary for `{task}`: Difficulty, Opus/GPT scores, "
                    "and full Unit Tests Results table (`prompts/trivial-fix-invoke.md` §1)."
                ),
            )
        easy_label = bool(re.search(r"\bEASY\b", text, re.I)) or summary.difficulty == "easy"
        router = "prompts/trivial-fix-invoke.md"
        case, case_why = _pick_trivial_case(low, text, summary)
        if case != "prompts/trivial-case-6.md" and (
            easy_label or summary.trivial_easy or summary.agents_easy
        ):
            case = "prompts/trivial-case-6.md"
            case_why = "TRIVIAL/EASY summary — Case 6 + trivial-fix-invoke.md (LOCKED)."
        return Route(
            router=router,
            case_file=case,
            phase="D",
            reason=f"Summary TRIVIAL/EASY → `{router}` → {case}. {case_why}",
            confidence="high",
            summary_note=_summary_line(summary),
        )

    # --- 8. MEDIUM ---
    if summary.difficulty == "medium" or "medium" in tagged:
        case, case_why = _pick_medium_case(summary, low)
        return Route(
            router="prompts/medium.md",
            case_file=case,
            phase="D",
            reason=f"Problem = **MEDIUM** → medium.md → {case}. {case_why}",
            confidence="medium",
            summary_note=_summary_line(summary),
        )

    # --- 9. HARD / not solvable / 0%-forever ---
    if (
        summary.difficulty == "hard"
        or summary.not_solvable
        or summary.zero_forever
        or "hard" in tagged
        or _any([r"\bunfair\b"], low)
    ):
        case, case_why = _pick_hard_case(summary, low)
        return Route(
            router="prompts/hard.md",
            case_file=case,
            phase="D",
            reason=f"Problem = **HARD / not solvable** → hard.md → {case}. {case_why}",
            confidence="medium",
            summary_note=_summary_line(summary),
        )

    # --- 9. @-tag only, thin summary ---
    if tagged:
        name = tagged[0]
        if name == "oracleFix":
            return Route(
                router="prompts/oracleFix.md",
                case_file=None,
                phase="D (oracle)",
                reason="You @-tagged oracle — confirm summary shows oracle/zip failure before editing.",
                confidence="low",
                summary_note="Summary lacks oracle signals — verify this is really an oracle issue.",
                ask="Does platform say **Oracle solution failed** or oracle reward **0**? If not, paste full summary.",
            )
        mapping = {
            "trivial": ("prompts/trivial.md", "D"),
            "medium": ("prompts/medium.md", "D"),
            "hard": ("prompts/hard.md", "D"),
            "reviewer": ("prompts/reviewer.md", "D′"),
            "audit": ("prompts/audit.md", "C"),
            "newidea": ("prompts/newidea.md", "A"),
        }
        router, phase = mapping.get(name, ("prompts/hard.md", "D"))
        return Route(
            router=router,
            case_file=None,
            phase=phase,
            reason=f"@-tagged {name}.md — **re-analyze summary** and confirm this router fits.",
            confidence="low",
            summary_note=_summary_line(summary) or "No parseable summary fields.",
            ask="Paste Difficulty, Status, Agent Performance, and per-test pass table.",
        )

    return Route(
        router="(analyze summary first)",
        case_file=None,
        phase="?",
        reason="Could not classify problem from summary.",
        confidence="low",
        summary_note=_summary_line(summary) or "No signals detected.",
        ask="Paste platform summary: Difficulty, Status, Agent Performance, Unit Tests (per-test passes).",
    )


def _summary_line(s: Summary) -> str:
    if not s.signals:
        return "Parsed summary: (no strong fields — read paste literally)"
    return "Parsed summary: " + "; ".join(s.signals)


def _enrich_route(route: Route, prompt: str, tagged: list[str]) -> Route:
    """Attach internal ENGINE_1..7 id (policy injected via build_route_context)."""
    if enrich_engine_from_prompt is not None:
        route.engine = enrich_engine_from_prompt(
            route.phase, route.router, prompt, tagged
        )
    return route


def _is_idea_generation(prompt: str, tagged: list[str], route: Route) -> bool:
    if route.phase.startswith("A") or "newidea" in tagged:
        return True
    low = prompt.lower()
    return _any(
        [
            r"generate\s+ideas",
            r"gen\s+ideas",
            r"new\s+idea",
            r"brainstorm",
            r"@IDEAS RULES",
            r"prompts/newidea",
        ],
        low,
    )


_IDEA_ASK_ONLY = re.compile(
    r"^(?:@NEWIDEA(?:\s+PROMPT)?|@prompts/newidea\.md|gen\s+ideas|generate\s+ideas|"
    r"brainstorm|aap gen karo)[\s.!]*$",
    re.I,
)


def _idea_intake_complete(prompt: str, tagged: list[str]) -> bool:
    """True when user supplied language + domain + idea (not bare 'gen ideas')."""
    stripped = prompt.strip()
    if _IDEA_ASK_ONLY.match(stripped):
        return False
    if "newidea" in tagged and len(stripped) < 45:
        return False
    low = stripped.lower()
    lang_hit = _any(
        [r"language\s*:", r"lang\s*:", r"primary language"],
        low,
    ) or _any(
        [
            r"\brust\b",
            r"\bgolang\b",
            r"\bgo\b",
            r"\bbash\b",
            r"\bjava\b",
            r"\btypescript\b",
            r"\bnode\b",
            r"\bpython\b",
            r"\bc\+\+\b",
            r"\bkotlin\b",
            r"\bruby\b",
            r"\bphp\b",
        ],
        low,
    )
    domain_hit = _any([r"domain\s*:", r"industry\s*:", r"scenario\s*:"], low)
    idea_hit = _any(
        [
            r"idea\s*:",
            r"task idea",
            r"concept\s*:",
            r"\bcli\b",
            r"\brepair\b",
            r"\bfix\b",
            r"\bbroken\b",
            r"\breplay\b",
            r"\bexport\b",
            r"\baudit\b",
        ],
        low,
    )
    if not lang_hit or len(stripped) < 50:
        return False
    if domain_hit and (idea_hit or len(stripped) >= 80):
        return True
    if idea_hit and len(stripped) >= 70:
        return True
    return False


def _is_readonly_task_work(prompt: str, tagged: list[str]) -> bool:
    low = prompt.lower()
    if _any(
        [
            r"read[\s-]?only",
            r"do not edit",
            r"don't edit",
            r"don'?t modify",
            r"audit only",
            r"no edits?",
            r"without (?:editing|modifying)",
            r"inspect only",
        ],
        low,
    ):
        return True
    return "audit" in tagged and not _any(
        [r"\bfix\b", r"\bimplement\b", r"\bbuild\b", r"\brevise\b", r"\bharden\b"],
        low,
    )


def _must_run_full_pipeline(prompt: str, tagged: list[str], task: str | None, route: Route) -> bool:
    """Any task path work → CREATE finish unless explicitly read-only."""
    if not task:
        return False
    if _is_readonly_task_work(prompt, tagged):
        return False
    return True


def _is_task_create(prompt: str, tagged: list[str], task: str | None, route: Route) -> bool:
    if _must_run_full_pipeline(prompt, tagged, task, route):
        return True
    if not task:
        return False
    low = prompt.lower()
    if route.phase.startswith("A"):
        return _any(
            [r"\bbuild it\b", r"implement", r"@CREATE", r"phase b", r"create only"],
            low,
        )
    if _is_idea_generation(prompt, tagged, route) and not _any(
        [r"implement", r"build task", r"build it", r"phase [cd]", r"@CREATE", r"create only"],
        low,
    ):
        return False
    if _any(
        [
            r"@CREATE",
            r"new-task-pipeline",
            r"phase [bd]\b",
            r"phase [cd]\b.*implement",
            r"create.*tasks/",
            r"implement.*tasks/",
            r"build.*tasks/",
            r"after_create\.sh",
        ],
        low,
    ):
        return True
    if "create" in tagged:
        return True
    return route.phase in ("B", "C", "D") and _any([r"implement", r"build", r"create task"], low)


def _anti_spam_automation_block(
    prompt: str, tagged: list[str], task: str | None, route: Route
) -> str:
    """Run anti-spam checks automatically — user never runs scripts manually."""
    lines: list[str] = [
        "",
        "**Anti-spam + post-create audit automation (AUTO — hooks on save + prompt submit)**",
        "",
        "On task file save: **post_create_audit_loop.py** (static Phase E) + **unacceptable_class_gate.py**.",
        "On ideas draft / idea prompt: **idea_similarity_gate.py**.",
        "Reports: `jobs-local/anti-spam-hook-last.txt`, `post-create-audit-last.json`, `unacceptable-class-gate-last.json`",
        "",
    ]

    if _is_idea_generation(prompt, tagged, route):
        if _idea_intake_complete(prompt, tagged):
            if write_ideas_draft_template is not None:
                write_ideas_draft_template()
            lines.extend(
                [
                    "**Ideas (similarity turn):** User gave lang+domain+idea — "
                    "scan `tasks/`, `pending/`, `_accepted-tasks/`, `tasksubmit/` only.",
                    "Optional: one entry in `jobs-local/ideas-draft.json` for hook screen **after** user's idea.",
                    "**Forbidden:** batch idea lists · `@CREATE` / new `tasks/` without user **build** + similarity PASS.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "**Ideas (ASK FIRST):** Ask language, domain, user's idea — **do not** generate ideas.",
                    "**Do not** write `jobs-local/ideas-draft.json` until user provides their idea.",
                    "",
                ]
            )

    if task and _must_run_full_pipeline(prompt, tagged, task, route):
        lines.extend(
            [
                f"## MANDATORY — full pipeline for `{task}` (user does not repeat)",
                "",
                "Standing: `.cursor/rules/sanjana-standing-requirements.mdc` §0 + §L.",
                "",
                "1. Fix audit **High → Medium** in `tasks/` or `pending/` tree (same session).",
                f"2. Run: `./scripts/create_finish_to_zip.sh {task}` (**no** `--skip-audit` / `--skip-harbor`).",
                "3. Canonical ECR `FROM` + anti-spam sim **0.0** + unacceptable **8/8** — automatic inside pack.",
                "4. End turn with `tasksubmit/" + task + ".zip` **or** `jobs-local/create-finish-last.json` BLOCKED + fixes.",
                "",
                "**Forbidden:** stop after CREATE without finish · ask permission for harbor/zip/ECR.",
                "",
            ]
        )
    elif _is_task_create(prompt, tagged, task, route) or task:
        lines.extend(
            [
                f"**Task `{task or '…'}`:** post-create pipeline on save (audit + 8/8 + finish → zip).",
                "",
            ]
        )

    if handle_prompt_submit is not None:
        is_ideas = _is_idea_generation(prompt, tagged, route)
        force_pipe = _must_run_full_pipeline(prompt, tagged, task, route) if task else False
        _code, auto_ctx = handle_prompt_submit(
            task,
            is_ideas=is_ideas,
            prompt=prompt,
            force_pipeline=force_pipe,
        )
        if auto_ctx:
            lines.extend(["**Latest auto-run (just now):**", "", auto_ctx, ""])

    return "\n".join(lines)


def format_context(route: Route, task: str | None, tagged: list[str], prompt: str = "") -> str:
    if build_route_context is not None:
        ctx = build_route_context(
            engine=route.engine,
            phase=route.phase,
            router=route.router,
            case_file=route.case_file,
            reason=route.reason,
            confidence=route.confidence,
            task=task,
            tagged=tagged,
            summary_note=route.summary_note,
            ask=route.ask,
        )
        auto = _anti_spam_automation_block(prompt, tagged, task, route)
        if auto:
            ctx = ctx + "\n" + auto
        trivial_block = _trivial_fixup_invoke_block(task, route)
        if trivial_block:
            ctx = ctx + "\n" + trivial_block
        reviewer_block = _reviewer_feedback_block(task, route)
        if reviewer_block:
            ctx = ctx + "\n" + reviewer_block
        return ctx

    # Fallback if scripts/ not on path
    return f"## {TERMINUS_ENGINE}\nRouter: {route.router}\nPhase: {route.phase}\n"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = data.get("prompt") or ""
    attachments = data.get("attachments") or []
    tagged = _tagged_prompts(prompt, attachments)
    task = _resolve_task(prompt)

    triggers = _hook_should_run(prompt, tagged, task)
    if not triggers:
        print(json.dumps({"continue": True}))
        return 0

    r = route(prompt, attachments)
    r = _enrich_route(r, prompt, tagged)
    ctx = format_context(r, task, tagged, prompt)
    print(json.dumps({"continue": True, "additional_context": ctx}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
