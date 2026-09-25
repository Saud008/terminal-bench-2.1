"""Terminus phase routing — which ENGINE + consolidated .mdc file."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINES_DIR = REPO_ROOT / ".cursor" / "rules" / "engines"

ENGINE_0_HUB = "ENGINE_0"
ENGINE_1_IDEAS = "ENGINE_1"
ENGINE_2_ANTI_SPAM = "ENGINE_2"
ENGINE_3_CREATE = "ENGINE_3"
ENGINE_4_AUDIT = "ENGINE_4"
ENGINE_5_VERIFY = "ENGINE_5"
ENGINE_6_ZIP = "ENGINE_6"
ENGINE_7_REVISE = "ENGINE_7"

PHASE_LABELS: dict[str, str] = {
    ENGINE_1_IDEAS: "IDEAS",
    ENGINE_2_ANTI_SPAM: "ANTI_SPAM",
    ENGINE_3_CREATE: "CREATE",
    ENGINE_4_AUDIT: "AUDIT",
    ENGINE_5_VERIFY: "VERIFY",
    ENGINE_6_ZIP: "ZIP",
    ENGINE_7_REVISE: "REVISE",
}

ENGINE_MDC: dict[str, str] = {
    ENGINE_1_IDEAS: "ENGINE_1_ideas.mdc",
    ENGINE_2_ANTI_SPAM: "ENGINE_2_anti_spam.mdc",
    ENGINE_3_CREATE: "ENGINE_3_create.mdc",
    ENGINE_4_AUDIT: "ENGINE_4_audit.mdc",
    ENGINE_5_VERIFY: "ENGINE_5_verify.mdc",
    ENGINE_6_ZIP: "ENGINE_6_zip.mdc",
    ENGINE_7_REVISE: "ENGINE_7_revise.mdc",
}


def mdc_path_for_engine(engine: str) -> Path:
    fname = ENGINE_MDC.get(engine, ENGINE_MDC[ENGINE_7_REVISE])
    return ENGINES_DIR / fname


def resolve_engine(
    phase: str,
    router: str,
    *,
    verify: bool = False,
    zip_phase: bool = False,
    anti_spam_only: bool = False,
) -> str:
    if anti_spam_only:
        return ENGINE_2_ANTI_SPAM
    if zip_phase:
        return ENGINE_6_ZIP
    if verify:
        return ENGINE_5_VERIFY
    if phase == "A" or "newidea" in router.lower():
        return ENGINE_1_IDEAS
    if "b" in phase.lower() and "create" in phase.lower():
        return ENGINE_3_CREATE
    if phase == "C" or "audit" in router.lower():
        return ENGINE_4_AUDIT
    if "oracle" in phase.lower() or "oraclefix" in router.lower():
        return ENGINE_7_REVISE
    if "d′" in phase or "reviewer" in router.lower():
        return ENGINE_7_REVISE
    if phase.startswith("D") or phase == "?":
        return ENGINE_7_REVISE
    return ENGINE_7_REVISE


def detect_verify_zip(prompt: str) -> tuple[bool, bool]:
    low = prompt.lower()
    verify = any(
        x in low
        for x in (
            "pre-upload",
            "pre-zip",
            "oracle and nop",
            "oracle + nop",
            "run oracle",
            "run nop",
            "@verify",
            "verify rules",
            "recheck from scratch",
            "phase e",
            "phase f′",
            "phase f'",
            "first-submit",
            "first submit",
        )
    )
    zip_phase = any(
        x in low
        for x in (
            "pack_zip",
            "pack zip",
            "@zip",
            "zip rules",
            "ready to submit",
            "tasksubmit/",
            "phase g",
            "phase f\b",
        )
    )
    return verify, zip_phase


def no_easy_upload_footer(engine: str) -> list[str]:
    """HARD target ≤20% — blocks zip after platform EASY until Case 6 + post-harden smoke."""
    if engine not in (ENGINE_5_VERIFY, ENGINE_6_ZIP, ENGINE_7_REVISE):
        return []
    return [
        "",
        "### No EASY upload lock (LOCKED — HARD target ≤20%)",
        "",
        "`pack_zip.sh` runs **after** F′:",
        "",
        "```bash",
        "python3 scripts/preupload_agent_calibration.py --pack-gate --task-dir tasks/<name>",
        "python3 scripts/preupload_difficulty_design_gate.py --pack-gate --task-dir tasks/<name>",
        "```",
        "",
        "- Platform **EASY/TRIVIAL** paste → Case 6 only; zip blocked until worst **≤20%** + `--post-harden`",
        "- `difficulty = \"hard\"` required; per-test ≥75% at 9/10 in summary → redesign",
        "",
        "Record after local smoke: `--record --opus 1/5 --gpt 2/5 --post-harden`",
        "Policy: `shared/no-easy-upload-lock.mdc`",
        "Override (user explicit only): `TERMINUS_AGENT_CALIBRATION_SKIP=1` / `TERMINUS_DIFFICULTY_DESIGN_SKIP=1`",
    ]


def standing_requirements_footer() -> list[str]:
    """Inject on every ENGINE turn — user must not repeat standing defaults."""
    return [
        "",
        "### Sanjana standing requirements (LOCKED — do not ask user to repeat)",
        "",
        "1. **After CREATE Phase D → auto E→F→F′→G** — same turn, **no** stop at “task created”",
        "2. **Hook on save** runs audit + unacceptable-class + `create_finish_to_zip` (zip if gates pass)",
        "3. **Agent MUST** run `./scripts/create_finish_to_zip.sh <name>` until exit **0** if hook did not zip",
        "4. **Reviewer instruction issues → no hints** in `instruction.md` — docs + tests only",
        "5. **pack_zip.sh only** · ECR auto — user runs no manual scripts",
        "6. **Pack anti-spam sim must be 0.0** — if sim > 0 fix task completely (§K) before zip",
        "7. **`rubrics/<slug>.md`** required before pack — **positive cumulative 10–40** per block (`platform_rubric_gate.py`)",
        "8. **`submission-explanations/<slug>.md`** auto-drafted before pack — **edit in your words** for platform form",
        "",
        "Full list: `shared/sanjana-standing-requirements.mdc`",
    ]


def platform_rubric_footer(engine: str) -> list[str]:
    """Platform rubric — positive cumulative 10–40 per block."""
    if engine not in (
        ENGINE_3_CREATE,
        ENGINE_5_VERIFY,
        ENGINE_6_ZIP,
        ENGINE_7_REVISE,
    ):
        return []
    return [
        "",
        "### Platform rubric (LOCKED — 10–40 positive cumulative)",
        "",
        "Before `pack_zip.sh`:",
        "",
        "```bash",
        "python3 scripts/write_platform_rubric.py --slug <name> --lines-file /tmp/rubric.txt",
        "python3 scripts/platform_rubric_gate.py --check --slug <name>",
        "```",
        "",
        "- File: `rubrics/<slug>.md` — **not** in zip",
        "- Sum **+1/+2/+3/+5** lines only → **10–40** per block (each `# Rubric N` for milestones)",
        "- ≥3 negatives overall; scores never **4**",
        "- Policy: `shared/platform-rubric-gate.mdc`",
        "- Override (user explicit only): `TERMINUS_PLATFORM_RUBRIC_SKIP=1`",
    ]


def submission_explanations_footer(engine: str) -> list[str]:
    """Platform upload form — Difficulty / Solution / Verification paragraphs."""
    if engine not in (
        ENGINE_3_CREATE,
        ENGINE_5_VERIFY,
        ENGINE_6_ZIP,
        ENGINE_7_REVISE,
    ):
        return []
    return [
        "",
        "### Submission explanations (LOCKED — platform form)",
        "",
        "`create_finish_to_zip.sh` auto-drafts before `pack_zip.sh`:",
        "",
        "```bash",
        "python3 scripts/write_submission_explanations.py --slug <name> --draft",
        "python3 scripts/submission_explanations_gate.py --check --slug <name>",
        "```",
        "",
        "- File: `submission-explanations/<slug>.md` — **not** in zip",
        "- Phase H: paste three paragraphs in chat **and** give file path",
        "- **Edit in your own words** before pasting on Snorkel submit form",
        "- Policy: `shared/submission-explanations-gate.mdc`",
        "- Override (user explicit only): `TERMINUS_SUBMISSION_EXPLANATIONS_SKIP=1`",
    ]


def idea_gate_footer(engine: str) -> list[str]:
    """Ideas similarity gate — block >0.10; auto CREATE when sim==0."""
    if engine not in (ENGINE_1_IDEAS, ENGINE_3_CREATE):
        return []
    return [
        "",
        "### Idea + task-generation gates (LOCKED)",
        "",
        "After user gives language + domain + idea:",
        "",
        "1. **No debugging objective** — fix/repair/patch/broken-repo ideas BLOCK (`task-generation-mandatory.mdc`)",
        "2. **Similarity** — run:",
        "",
        "```bash",
        "python3 scripts/idea_similarity_gate.py --language ... --domain ... --title ... --summary ...",
        "```",
        "",
        "- **debugging-shaped idea** → BLOCK — reframe as new capability",
        "- **weighted > 0.10** → BLOCK — no CREATE",
        "- **weighted == 0.0** → AUTO_CREATE — start Phase A immediately (no “build it”)",
        "- **0 < sim ≤ 0.10** → PASS — user confirms → CREATE",
        "",
        "Reports: `jobs-local/idea-similarity-gate-last.json` · `jobs-local/task-generation-gate-last.json`",
        "Full workflow: `ideas/idea-similarity-gate.mdc` · `shared/task-generation-mandatory.mdc`",
    ]


def task_generation_footer(engine: str) -> list[str]:
    """No debugging / repair-shaped tasks — pack + create."""
    if engine not in (
        ENGINE_1_IDEAS,
        ENGINE_3_CREATE,
        ENGINE_6_ZIP,
        ENGINE_7_REVISE,
    ):
        return []
    return [
        "",
        "### Task generation (LOCKED — no debugging, no software-engineering)",
        "",
        "Hard acceptance **7/7** required before zip. Functional repo — agent builds/analyzes something **new**.",
        "",
        "```bash",
        "python3 scripts/repository_state_gate.py --pack-gate --task-dir tasks/<name>",
        "```",
        "",
        "On FAIL: `shared/repository-state-fail-fix.mdc` (LOCKED fix in place).",
        "Checks: H1 not debugging · H2 not broken repo · H3 not fix existing · H4 new capability ·",
        "H5 not find-bug/make-tests-pass · H6 accepted category · H7 not repair workflow.",
        "",
        "Policy: `shared/task-generation-mandatory.mdc`",
        "Override (user explicit only): `TERMINUS_TASK_GENERATION_SKIP=1`",
    ]


def create_audit_loop_footer(engine: str) -> list[str]:
    """Mandatory CREATE Phase E auto audit loop — injected on ENGINE_3 only."""
    if engine != ENGINE_3_CREATE:
        return []
    return [
        "",
        "### Post-create audit loop (LOCKED — auto, no user ask)",
        "",
        "**Hook (automatic):** saving task files runs `post_create_audit_loop.py` + `unacceptable_class_gate.py`.",
        "Reports: `jobs-local/post-create-audit-last.json`, `anti-spam-hook-last.txt`.",
        "",
        "After Phase D → agent **immediately** enters Phase E per `create/post-create-audit-loop.mdc`:",
        "",
        "1. Read hook static report (round 1–4 tracked in JSON)",
        "2. Semantic audit: `prompts/audit.md` + AUDIT + REVIEWER + checklist",
        "3. Fix **High → Medium → optional Low** (Low never blocks zip)",
        "4. Stop when High=0 and Medium=0 (min 2 rounds if round 1 had blockers)",
        "5. **Auto:** `./scripts/create_finish_to_zip.sh <name>` until `tasksubmit/<name>.zip` exists",
        "   (hook also runs finish on every task file save — debounced 45s)",
        "",
        "**FORBIDDEN:** End CREATE turn without zip path OR explicit BLOCKED_* in `jobs-local/create-finish-last.json`.",
        "",
        "Optional manual: `./scripts/after_create.sh <name>` (audit round 1 only).",
        "**Do not ask** user to approve audit or zip after CREATE.",
    ]


def first_submit_engine_footer(engine: str) -> list[str]:
    """Mandatory CREATE first-upload lines injected by the rules engine hook."""
    if engine not in (ENGINE_3_CREATE, ENGINE_5_VERIFY, ENGINE_6_ZIP, ENGINE_4_AUDIT):
        return []
    return [
        "",
        "### First-submit acceptance gate (LOCKED — ENGINE + pack_zip hard block)",
        "",
        "`./scripts/pack_zip.sh` **will not zip** until Phase F′ PASS is recorded:",
        "",
        "```bash",
        "python3 scripts/first_submit_pack_gate.py --record --task-dir tasks/<name> \\",
        "  --oracle 1.0 --nop 0.0 \\",
        "  --probe 1=PASS --probe 3=PASS --probe 4=PASS --probe 5=PASS \\",
        "  --probe 1b=PASS --probe 7=PASS --probe 8=PASS   # Go/Rust/Bash export CLI",
        "./scripts/pack_zip.sh <name>",
        "```",
        "",
        "Check: `python3 scripts/first_submit_pack_gate.py --pack-gate --task-dir tasks/<name>`",
        "Report: `jobs-local/first-submit-last.txt`",
        "Skip only: slug in `scripts/platform_submissions.txt` OR user `TERMINUS_FIRST_SUBMIT_SKIP=1` in message.",
        "",
        "Before record: probes in `create/first-submit-acceptance-gate.mdc` + `revise/trivial-hardening-probes.mdc`.",
        "Resubmit after platform TRIVIAL → **ENGINE_7 REVISE** (not F′ alone).",
    ]


def unacceptable_class_footer(engine: str) -> list[str]:
    """All 8 unacceptable classes must PASS before zip — zero tolerance."""
    if engine not in (
        ENGINE_2_ANTI_SPAM,
        ENGINE_3_CREATE,
        ENGINE_5_VERIFY,
        ENGINE_6_ZIP,
        ENGINE_7_REVISE,
    ):
        return []
    return [
        "",
        "### Unacceptable-class gate (LOCKED — all 8 must PASS)",
        "",
        "`pack_zip.sh` runs **after** anti-spam:",
        "",
        "```bash",
        "python3 scripts/unacceptable_class_gate.py --pack-gate --task-dir tasks/<name>",
        "```",
        "",
        "**Not allowed (any FAIL → no zip):** TEMPLATED, COPY, DUPLICATE, FAMILY, SAME_LANE, SIBLING, FABRICATED, SYNTHETIC.",
        "",
        "Report: `jobs-local/unacceptable-class-gate-last.json`",
        "Policy: `shared/unacceptable-task-classes.mdc`",
        "Override (user explicit only): `TERMINUS_ANTI_SPAM_SKIP=1` on pack_zip.",
    ]
