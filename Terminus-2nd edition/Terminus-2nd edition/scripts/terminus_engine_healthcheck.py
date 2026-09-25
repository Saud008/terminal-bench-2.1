#!/usr/bin/env python3
"""Validate Terminus engine + hooks + pack gates wiring (run after rule/hook changes).

  python3 scripts/terminus_engine_healthcheck.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
ENGINES = REPO / ".cursor" / "rules" / "engines"
ARCHIVE = REPO / "archive" / "terminus-rules-mdc"
HOOKS = REPO / ".cursor" / "hooks"

ENGINE_FILES = [
    "ENGINE_1_ideas.mdc",
    "ENGINE_2_anti_spam.mdc",
    "ENGINE_3_create.mdc",
    "ENGINE_4_audit.mdc",
    "ENGINE_5_verify.mdc",
    "ENGINE_6_zip.mdc",
    "ENGINE_7_revise.mdc",
]

ENGINE_MARKERS = {
    "ENGINE_1_ideas.mdc": ("idea-similarity-gate.mdc", "IDEAS-ASK-FIRST"),
    "ENGINE_2_anti_spam.mdc": ("anti-spam-templated-submissions.mdc", "unacceptable-task-classes"),
    "ENGINE_3_create.mdc": ("post-create-audit-loop.mdc", "first-submit-acceptance-gate"),
    "ENGINE_4_audit.mdc": ("AUDIT-RULES.mdc", "reviewer-checklist"),
    "ENGINE_5_verify.mdc": ("VERIFY-RULES.mdc", "oracle-fix-g025-g027"),
    "ENGINE_6_zip.mdc": ("ZIP-RULES.mdc", "unacceptable_class_gate.py"),
    "ENGINE_7_revise.mdc": ("REVISE-RULES.mdc", "trivial-easy-difficulty-prompt-lock"),
}

PACK_ZIP_GATES = [
    ("migrate_dockerfile_canonical_ecr.py", "canonical ECR"),
    ("ensure_subcategories_empty.py", "subcategories []"),
    ("ensure_category_allowed.py", "category gate"),
    ("repository_state_gate.py", "repository-state 7/7"),
    ("terminus_anti_spam_auto.py", "anti-spam pack"),
    ("unacceptable_class_gate.py", "unacceptable-class 8/8"),
    ("task_uniqueness_gate.py", "task uniqueness distinct dims"),
    ("first_submit_pack_gate.py", "first-submit F′"),
    ("preupload_agent_calibration.py", "agent calibration HARD ≤20%"),
    ("preupload_difficulty_design_gate.py", "difficulty design gate"),
    ("preupload_trivial_shape_gate.py", "trivial shape S1–S7"),
    ("submission_explanations_gate.py", "submission explanations"),
    ("platform_rubric_gate.py", "platform rubric 10–40"),
    ("terminus_ci_check.py", "CI preflight"),
]

REQUIRED_SCRIPTS = [
    "terminus_rules_engine.py",
    "terminus_engine_registry.py",
    "terminus_engine_healthcheck.py",
    "build_consolidated_rules.py",
    "terminus_anti_spam_auto.py",
    "terminus_anti_spam_check.py",
    "anti_spam_pipeline.py",
    "anti_spam_hook_runner.py",
    "idea_similarity_gate.py",
    "unacceptable_class_gate.py",
    "first_submit_pack_gate.py",
    "preupload_agent_calibration.py",
    "preupload_difficulty_design_gate.py",
    "preupload_trivial_shape_gate.py",
    "post_create_audit_loop.py",
    "after_create.sh",
    "terminus_ci_check.py",
    "terminus_verify_submit.py",
    "reviewer_feedback_gate.py",
    "terminus_accepted_feedback_gates.py",
    "write_submission_explanations.py",
    "submission_explanations_gate.py",
    "write_platform_rubric.py",
    "platform_rubric_gate.py",
    "rubric_policy.py",
    "repository_state_gate.py",
    "task_generation_gate.py",
    "task_generation_policy.py",
    "task_uniqueness_gate.py",
    "task_uniqueness_policy.py",
    "pack_zip.sh",
]


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def warn(msg: str) -> None:
    print(f"  WARN  {msg}")


def main() -> int:
    errors = 0
    warnings = 0

    print("# Terminus engine healthcheck\n")

    # --- ENGINE bundles ---
    print("## ENGINE bundles (7)")
    for name in ENGINE_FILES:
        p = ENGINES / name
        if not p.is_file() or p.stat().st_size < 10_000:
            fail(f"{name} missing or too small")
            errors += 1
            continue
        ok(f"{name} ({p.stat().st_size // 1024} KiB)")
        m1, m2 = ENGINE_MARKERS[name]
        text = p.read_text(encoding="utf-8", errors="replace")
        if m1 not in text:
            fail(f"{name} missing marker `{m1}` — rebuild: build_consolidated_rules.py")
            errors += 1
        elif m2 not in text:
            fail(f"{name} missing marker `{m2}` — rebuild: build_consolidated_rules.py")
            errors += 1

    hub = REPO / ".cursor" / "rules" / "terminus.mdc"
    standing = REPO / ".cursor" / "rules" / "sanjana-standing-requirements.mdc"
    if hub.is_file():
        ok("terminus.mdc hub lists ENGINE_1–7")
    else:
        fail("terminus.mdc hub missing")
        errors += 1
    if standing.is_file():
        st = standing.read_text(encoding="utf-8", errors="replace")
        fm = st.split("---", 2)
        front = fm[1] if len(fm) > 1 and st.startswith("---") else fm[0]
        if "alwaysApply: true" in front:
            ok("sanjana-standing-requirements.mdc alwaysApply: true (LOCKED)")
        else:
            fail("sanjana-standing-requirements.mdc must have alwaysApply: true")
            errors += 1
        for needle in (
            "create_finish_to_zip.sh",
            "unacceptable_class_gate",
            "submission-explanations",
            "no hints",
            "pack_zip.sh",
        ):
            if needle.lower() in st.lower():
                ok(f"standing requirements → {needle}")
            else:
                fail(f"standing requirements missing {needle}")
                errors += 1
    else:
        fail(".cursor/rules/sanjana-standing-requirements.mdc missing (LOCKED always-on)")
        errors += 1

    # --- Archive sources ---
    print("\n## Archive → bundle sources")
    if not ARCHIVE.is_dir():
        fail(f"missing {ARCHIVE}")
        errors += 1
    else:
        sys.path.insert(0, str(SCRIPTS))
        from build_consolidated_rules import BUNDLES, SHARED_CORE  # noqa: WPS433

        missing_src: list[str] = []
        for _fname, (_title, _desc, sources) in BUNDLES.items():
            for rel in sources:
                if not (ARCHIVE / rel).is_file():
                    missing_src.append(rel)
        if missing_src:
            fail(f"{len(missing_src)} bundle source(s) missing: {missing_src[:8]}")
            errors += 1
        else:
            ok(f"all bundle archive sources present ({len(BUNDLES)} engines)")

        if "shared/unacceptable-task-classes.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing unacceptable-task-classes.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes unacceptable-task-classes.mdc")

        if "shared/trivial-first-upload-lock.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing trivial-first-upload-lock.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes trivial-first-upload-lock.mdc")

        if "shared/trivial-fix-invoke-mandatory-steps.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing trivial-fix-invoke-mandatory-steps.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes trivial-fix-invoke-mandatory-steps.mdc")

        if "shared/no-easy-upload-lock.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing no-easy-upload-lock.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes no-easy-upload-lock.mdc")

        if "shared/block-trivial-platform-acceptance.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing block-trivial-platform-acceptance.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes block-trivial-platform-acceptance.mdc")

        if "shared/submission-explanations-gate.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing submission-explanations-gate.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes submission-explanations-gate.mdc")

        if "shared/repository-state-fail-fix.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing repository-state-fail-fix.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes repository-state-fail-fix.mdc")

        if "shared/forbidden-repair-objectives-gate.mdc" not in SHARED_CORE:
            fail("SHARED_CORE missing forbidden-repair-objectives-gate.mdc")
            errors += 1
        else:
            ok("SHARED_CORE includes forbidden-repair-objectives-gate.mdc")

    # --- Registry ---
    print("\n## Registry + footers")
    from terminus_engine_registry import (  # noqa: E402
        ENGINE_MDC,
        create_audit_loop_footer,
        first_submit_engine_footer,
        idea_gate_footer,
        mdc_path_for_engine,
        unacceptable_class_footer,
        submission_explanations_footer,
        platform_rubric_footer,
    )
    from terminus_engine_registry import ENGINE_3_CREATE, ENGINE_6_ZIP, ENGINE_7_REVISE  # noqa: E402

    for eng, fname in ENGINE_MDC.items():
        path = mdc_path_for_engine(eng)
        if path.name != fname:
            fail(f"{eng} maps to {path.name}, expected {fname}")
            errors += 1
    chk = SCRIPTS / "terminus_anti_spam_check.py"
    if chk.is_file() and "PACK_SIM_MUST_BE_ZERO" in chk.read_text(encoding="utf-8"):
        ok("PACK_SIM_MUST_BE_ZERO standing gate in terminus_anti_spam_check.py")
    else:
        fail("PACK_SIM_MUST_BE_ZERO missing from terminus_anti_spam_check.py")
        errors += 1

    pack_sh = SCRIPTS / "pack_zip.sh"
    if pack_sh.is_file():
        pack_txt = pack_sh.read_text(encoding="utf-8")
        required_in_pack = (
            "migrate_dockerfile_canonical_ecr.py",
            "repository_state_gate.py",
            "terminus_anti_spam_auto.py",
            "unacceptable_class_gate.py",
            "task_uniqueness_gate.py",
            "first_submit_pack_gate.py",
            "preupload_agent_calibration.py",
            "preupload_difficulty_design_gate.py",
            "preupload_trivial_shape_gate.py",
            "submission_explanations_gate.py",
            "platform_rubric_gate.py",
            "terminus_ci_check.py",
            "terminus_verify_submit.py",
        )
        missing_pack = [s for s in required_in_pack if s not in pack_txt]
        if missing_pack:
            fail(f"pack_zip.sh missing gates: {missing_pack}")
            errors += 1
        elif "TERMINUS_NO_HARBOR" in pack_txt and "harbor LLMaJ" in pack_txt.lower():
            fail("pack_zip.sh still wires harbor LLMaJ — remove (local CI only)")
            errors += 1
        else:
            ok("pack_zip.sh full gate chain wired (ECR → anti-spam → 8-class → F′ → calibration → design → shape → CI → verify)")
    else:
        fail("pack_zip.sh missing")
        errors += 1

    if errors == 0:
        ok("ENGINE_1–7 ↔ ENGINE_*.mdc mapping")

    if not idea_gate_footer("ENGINE_1"):
        fail("idea_gate_footer missing for ENGINE_1")
        errors += 1
    else:
        ok("idea_gate_footer → ENGINE_1/3")

    if not create_audit_loop_footer(ENGINE_3_CREATE):
        fail("create_audit_loop_footer missing for ENGINE_3")
        errors += 1
    else:
        ok("create_audit_loop_footer → ENGINE_3")

    if not first_submit_engine_footer(ENGINE_6_ZIP):
        fail("first_submit_engine_footer missing for ENGINE_6")
        errors += 1
    else:
        ok("first_submit_engine_footer → ENGINE_6")

    from terminus_engine_registry import no_easy_upload_footer  # noqa: WPS433

    if not no_easy_upload_footer(ENGINE_7_REVISE):
        fail("no_easy_upload_footer missing for ENGINE_7")
        errors += 1
    else:
        ok("no_easy_upload_footer → ENGINE_5/6/7")

    if not unacceptable_class_footer(ENGINE_6_ZIP):
        fail("unacceptable_class_footer missing for ENGINE_6")
        errors += 1
    else:
        ok("unacceptable_class_footer → ENGINE_2/3/5/6/7")

    if not submission_explanations_footer(ENGINE_6_ZIP):
        fail("submission_explanations_footer missing for ENGINE_6")
        errors += 1
    else:
        ok("submission_explanations_footer → ENGINE_3/5/6/7")

    if not platform_rubric_footer(ENGINE_6_ZIP):
        fail("platform_rubric_footer missing for ENGINE_6")
        errors += 1
    else:
        ok("platform_rubric_footer → ENGINE_3/5/6/7")

    from terminus_engine_registry import standing_requirements_footer  # noqa: WPS433

    if not standing_requirements_footer():
        fail("standing_requirements_footer empty")
        errors += 1
    else:
        ok("standing_requirements_footer → all ENGINE hook context")

    eng7 = ENGINES / "ENGINE_7_revise.mdc"
    if eng7.is_file() and "no-easy-upload-lock" not in eng7.read_text(encoding="utf-8"):
        fail("ENGINE_7 missing no-easy-upload-lock.mdc embed")
        errors += 1
    else:
        ok("SHARED_CORE no-easy-upload-lock in ENGINE_7 bundle")

    eng1 = ENGINES / "ENGINE_1_ideas.mdc"
    if eng1.is_file() and "sanjana-standing-requirements" not in eng1.read_text(encoding="utf-8"):
        fail("ENGINE_1 missing sanjana-standing-requirements.mdc embed")
        errors += 1
    else:
        ok("SHARED_CORE sanjana-standing-requirements in ENGINE bundles")

    # --- Hooks ---
    print("\n## Hooks")
    hooks_json = REPO / ".cursor" / "hooks.json"
    if hooks_json.is_file():
        data = json.loads(hooks_json.read_text(encoding="utf-8"))
        for hook_name in ("beforeSubmitPrompt", "postToolUse", "afterFileEdit"):
            if hook_name in data.get("hooks", {}):
                ok(f"hooks.json → {hook_name}")
            else:
                warn(f"hooks.json missing {hook_name}")
                warnings += 1
    else:
        fail("hooks.json missing")
        errors += 1

    for script in ("route-terminus-prompt.py", "anti-spam-auto-run.py"):
        p = HOOKS / script
        if p.is_file():
            ok(script)
        else:
            fail(f"missing hooks/{script}")
            errors += 1

    route = HOOKS / "route-terminus-prompt.py"
    if route.is_file():
        body = route.read_text(encoding="utf-8")
        if "terminus_rules_engine" in body and "build_route_context" in body:
            ok("route hook → terminus_rules_engine.build_route_context")
        else:
            fail("route hook not wired to terminus_rules_engine")
            errors += 1

    # --- Scripts ---
    print("\n## Automation scripts")
    for script in REQUIRED_SCRIPTS:
        if (SCRIPTS / script).is_file():
            ok(script)
        else:
            fail(f"missing scripts/{script}")
            errors += 1

    # --- pack_zip gate chain ---
    print("\n## pack_zip.sh gate chain (execution order)")
    pack = SCRIPTS / "pack_zip.sh"
    if not pack.is_file():
        fail("pack_zip.sh missing")
        errors += 1
    else:
        pack_text = pack.read_text(encoding="utf-8")
        last_pos = -1
        for needle, label in PACK_ZIP_GATES:
            pos = pack_text.find(needle)
            if pos < 0:
                fail(f"pack_zip.sh missing {needle} ({label})")
                errors += 1
            elif pos < last_pos:
                fail(f"pack_zip.sh wrong order: {label} before prior gate")
                errors += 1
            else:
                ok(f"pack_zip.sh → {label}")
                last_pos = pos

    after_create = SCRIPTS / "after_create.sh"
    if after_create.is_file():
        ac = after_create.read_text(encoding="utf-8")
        for needle in ("terminus_anti_spam_auto.py", "post_create_audit_loop.py", "create_finish_to_zip"):
            if needle in ac:
                ok(f"after_create.sh → {needle}")
            else:
                fail(f"after_create.sh missing {needle}")
                errors += 1

    finish = SCRIPTS / "create_finish_to_zip.py"
    if finish.is_file():
        finish_txt = finish.read_text(encoding="utf-8")
        ok("create_finish_to_zip.py present")
        if "ensure_submission_explanations" not in finish_txt:
            fail("create_finish_to_zip.py missing ensure_submission_explanations")
            errors += 1
        elif "ensure_platform_rubric" not in finish_txt:
            fail("create_finish_to_zip.py missing ensure_platform_rubric")
            errors += 1
        else:
            ok("create_finish_to_zip → platform rubric + submission explanations before pack")
    else:
        fail("create_finish_to_zip.py missing")
        errors += 1

    for name in (
        "trivial_easy_context.py",
        "trivial_easy_auto_finish.py",
        "trivial_easy_auto_finish.sh",
        "auto_easy_platform_automation.py",
    ):
        p = SCRIPTS / name
        if p.is_file():
            ok(f"{name} present")
        else:
            fail(f"{name} missing")
            errors += 1

    hook_runner = SCRIPTS / "anti_spam_hook_runner.py"
    if hook_runner.is_file():
        hr = hook_runner.read_text(encoding="utf-8")
        for needle in (
            "post_create_audit_loop.py",
            "unacceptable_class_gate.py",
            "run_repository_state_gate",
            "repository_state_gate.py",
            "run_create_finish",
            "run_trivial_easy_auto_finish",
            "has_trivial_easy_context",
            "save_trivial_easy_context_from_prompt",
            "skip_easy_finish",
            "run_gate_from_draft",
            "run_task_pipeline",
            "reviewer_feedback_gate.py",
            "save_reviewer_feedback_from_prompt",
            "run_reviewer_feedback_gate",
            "has_reviewer_feedback_context",
            "resolve_jobs_path",
        ):
            if needle in hr:
                ok(f"anti_spam_hook_runner → {needle}")
            else:
                fail(f"anti_spam_hook_runner missing {needle}")
                errors += 1
        route_body = route.read_text(encoding="utf-8") if route.is_file() else ""
        if "prompt=prompt" in route_body or "prompt=prompt)" in route_body:
            ok("route hook passes prompt → handle_prompt_submit")
        else:
            fail("route hook must pass prompt= to handle_prompt_submit")
            errors += 1

    print("\n## Route hook smoke (ENGINE selection)")
    route_tests = {
        "gen ideas": "IDEAS",
        "@AUDIT audit tasks/foo/": "AUDIT",
        "pre-upload tasks/foo": "VERIFY",
        "pack_zip tasks/foo": "ZIP",
        "Fix tasks/foo/ TRIVIAL": "REVISE",
        "@CREATE implement tasks/bar/": "CREATE",
    }
    for prompt, want in route_tests.items():
        proc = subprocess.run(
            [sys.executable, str(route)],
            input=json.dumps({"prompt": prompt}),
            capture_output=True,
            text=True,
            cwd=str(REPO),
        )
        try:
            out = json.loads(proc.stdout)
            ctx = out.get("additional_context", "")
            if f"phase `{want}`" in ctx:
                ok(f"'{prompt[:36]}' → {want}")
            else:
                fail(f"'{prompt}' expected phase {want}")
                errors += 1
            if want in ("ZIP", "CREATE", "REVISE") and "Unacceptable-class gate" not in ctx:
                fail(f"'{prompt}' missing unacceptable_class_footer in hook context")
                errors += 1
        except json.JSONDecodeError:
            fail(f"route hook invalid JSON for: {prompt}")
            errors += 1

    # --- jobs-local path resolution (writers → subfolders; readers → resolve) ---
    print("\n## jobs-local path resolution")
    sys.path.insert(0, str(SCRIPTS))
    from anti_spam_hook_runner import (  # noqa: WPS433
        has_reviewer_feedback_context,
        has_trivial_easy_context,
        save_reviewer_feedback_from_prompt,
        save_trivial_easy_context_from_prompt,
    )

    slug = "_healthcheck-path-probe"
    save_reviewer_feedback_from_prompt(
        slug,
        "Reviewer feedback for tasks/foo/: instruction paths must be absolute per audit.",
    )
    save_trivial_easy_context_from_prompt(slug, "Platform TRIVIAL opus 5/5 gpt 5/5")
    if has_reviewer_feedback_context(slug):
        ok("reviewer-feedback-context resolves after save")
    else:
        fail("reviewer-feedback-context not found after save")
        errors += 1
    if has_trivial_easy_context(slug):
        ok("trivial-easy-context resolves after save")
    else:
        fail("trivial-easy-context not found after save")
        errors += 1

    # --- Live rules layout ---
    print("\n## Live rules layout")
    live_rules = list((REPO / ".cursor" / "rules").glob("**/*.mdc"))
    engine_count = sum(1 for p in live_rules if p.parent.name == "engines")
    if engine_count == 7:
        ok(".cursor/rules/engines/ = 7 ENGINE_*.mdc bundles")
    else:
        warn(f"engines/ has {engine_count} files (expected 7)")

    # --- Workspace-root Cursor bridge (nested checkout) ---
    print("\n## Workspace-root hooks + rules (Cursor load path)")
    workspace_root = REPO.parent
    nested_name = REPO.name
    root_cursor = workspace_root / ".cursor"
    root_hooks = root_cursor / "hooks.json"
    root_rules = root_cursor / "rules"
    if workspace_root != REPO and (workspace_root / nested_name / "scripts" / "terminus_rules_engine.py").is_file():
        if root_hooks.is_file():
            root_data = json.loads(root_hooks.read_text(encoding="utf-8"))
            for hook_name in ("beforeSubmitPrompt", "postToolUse", "afterFileEdit"):
                entries = root_data.get("hooks", {}).get(hook_name, [])
                if not entries:
                    fail(f"workspace-root hooks.json missing {hook_name}")
                    errors += 1
                    continue
                cmd = entries[0].get("command", "")
                for script in ("route-terminus-prompt.py", "anti-spam-auto-run.py"):
                    if script in cmd and nested_name in cmd.replace("\\", "/"):
                        ok(f"workspace-root {hook_name} → {script}")
                        break
                else:
                    fail(f"workspace-root {hook_name} must reference {nested_name}/.cursor/hooks/")
                    errors += 1
        else:
            fail(f"workspace-root {root_hooks} missing — Cursor will not load hooks")
            errors += 1

        if root_rules.is_dir() and (root_rules / "terminus.mdc").is_file():
            ok("workspace-root .cursor/rules/ → terminus.mdc visible")
        else:
            fail(
                "workspace-root .cursor/rules/ missing — junction to inner repo required "
                f"(mklink /J \"{root_rules}\" \"{REPO / '.cursor' / 'rules'}\")"
            )
            errors += 1

        if root_rules.is_dir() and (root_rules / "engines" / "ENGINE_1_ideas.mdc").is_file():
            ok("workspace-root rules/engines/ ENGINE bundles visible")
        else:
            fail("workspace-root rules/engines/ not wired")
            errors += 1

        root_route = REPO / ".cursor" / "hooks" / "route-terminus-prompt.py"
        proc = subprocess.run(
            [sys.executable, str(root_route)],
            input=json.dumps({"prompt": "gen ideas"}),
            capture_output=True,
            text=True,
            cwd=str(workspace_root),
        )
        try:
            out = json.loads(proc.stdout)
            if "phase `IDEAS`" in out.get("additional_context", ""):
                ok("route hook smoke from workspace root cwd → IDEAS")
            else:
                fail("route hook from workspace root cwd did not return IDEAS phase")
                errors += 1
        except json.JSONDecodeError:
            fail(f"route hook invalid JSON from workspace root (stderr: {proc.stderr[:200]})")
            errors += 1
    else:
        ok("repo root = workspace root (no bridge required)")

    print(f"\n---\nResult: {errors} error(s), {warnings} warning(s)")
    if errors:
        print("Fix errors then: python3 scripts/build_consolidated_rules.py")
        return 1
    print("Engines + hooks + pack gates OK. Restart Cursor after hook changes.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(SCRIPTS))
    raise SystemExit(main())
