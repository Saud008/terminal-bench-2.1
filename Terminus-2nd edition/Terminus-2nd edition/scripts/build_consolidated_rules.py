#!/usr/bin/env python3
"""Merge archive/terminus-rules-mdc/ into 7 self-contained .cursor/rules/engines/*.mdc files.

Each bundle = shared core + phase sources (verbatim). Run after editing archive.

  python3 scripts/build_consolidated_rules.py
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARCHIVE = REPO / "archive" / "terminus-rules-mdc"
OUT = REPO / ".cursor" / "rules" / "engines"

SHARED_CORE = [
    "LOCKED.mdc",
    "shared/sanjana-standing-requirements.mdc",
    "shared/no-easy-upload-lock.mdc",
    "shared/block-trivial-platform-acceptance.mdc",
    "shared/trivial-first-upload-lock.mdc",
    "shared/trivial-fix-invoke-mandatory-steps.mdc",
    "shared/workflow-prompt-automation-lock.mdc",
    "shared/rubric-storage-lock.mdc",
    "shared/platform-rubric-gate.mdc",
    "shared/submission-explanations-gate.mdc",
    "shared/task-generation-mandatory.mdc",
    "shared/repository-state-requirement.mdc",
    "shared/repository-state-fail-fix.mdc",
    "shared/forbidden-repair-objectives-gate.mdc",
    "shared/task-uniqueness-gate.mdc",
    "shared/jobs-local-layout-lock.mdc",
    "shared/WORKFLOW-MAP.mdc",
    "shared/core.mdc",
    "shared/repo-workflow.mdc",
    "shared/prompt-router.mdc",
    "shared/problem-rule-loader.mdc",
    "shared/additive-rules-lock-index.mdc",
    "shared/unacceptable-task-classes.mdc",
]

BUNDLES: dict[str, tuple[str, str, list[str]]] = {
    "ENGINE_1_ideas.mdc": (
        "ENGINE_1 — IDEAS",
        "Ideas / newidea — corpus scan, anti-spam on ideas",
        SHARED_CORE
        + [
            "ideas/IDEAS-ASK-FIRST.mdc",
            "ideas/idea-similarity-gate.mdc",
            "ideas/IDEAS-RULES.mdc",
            "ideas/generate-ideas.mdc",
            "shared/accepted-corpus.mdc",
            "shared/anti-spam-templated-submissions.mdc",
            "create/safe-languages.mdc",
            "create/accepted-patterns.mdc",
        ],
    ),
    "ENGINE_2_anti_spam.mdc": (
        "ENGINE_2 — ANTI_SPAM",
        "Anti-spam / templated gate — pack and ideas",
        SHARED_CORE
        + [
            "shared/anti-spam-templated-submissions.mdc",
            "shared/anti-trivial.mdc",
        ],
    ),
    "ENGINE_3_create.mdc": (
        "ENGINE_3 — CREATE",
        "New task A→H pipeline, Dockerfile, structure",
        SHARED_CORE
        + [
            "create/CREATE-RULES.mdc",
            "create/new-task-pipeline-A-H.mdc",
            "create/creation-rules.mdc",
            "create/accepted-patterns.mdc",
            "create/safe-languages.mdc",
            "create/environment-no-ai-scaffolding.mdc",
            "ideas/idea-similarity-gate.mdc",
            "create/post-create-audit-loop.mdc",
            "create/first-submit-acceptance-gate.mdc",
            "audit/AUDIT-RULES.mdc",
            "reviewer/reviewer-checklist.mdc",
            "revise/trivial-hardening-probes.mdc",
            "revise/hardness.mdc",
            "shared/task-lifecycle.mdc",
            "shared/accepted-corpus.mdc",
            "shared/first-pass-blueprint.mdc",
            "shared/anti-trivial.mdc",
            "shared/spec.mdc",
            "shared/dockerfile.mdc",
            "shared/snorkel-dockerfile-image-best-practices.mdc",
            "shared/runtime-verifier.mdc",
            "shared/platform-preferences.mdc",
            "shared/canonical-base-image-gate.mdc",
            "shared/canonical-ecr-dockerfile-auto.mdc",
            "shared/instruction-prose-style.mdc",
            "shared/task-toml-subcategories-gate.mdc",
            "shared/task-toml-category-gate.mdc",
            "shared/allow-internet-gate.mdc",
            "shared/snorkel-platform-changelog-sync.mdc",
            "shared/test-sh-reward-block.mdc",
            "shared/difficulty-benchmark-models.mdc",
            "shared/anti-spam-templated-submissions.mdc",
        ],
    ),
    "ENGINE_4_audit.mdc": (
        "ENGINE_4 — AUDIT",
        "Read-only audit + reviewer checklist",
        SHARED_CORE
        + [
            "audit/AUDIT-RULES.mdc",
            "reviewer/REVIEWER-RULES.mdc",
            "reviewer/reviewer-checklist.mdc",
            "reviewer/common-errors-reference.mdc",
            "reviewer/ci-checks-reference.mdc",
            "reviewer/llmaj-checks-reference.mdc",
            "reviewer/agent-review-reference.mdc",
            "shared/anti-trivial.mdc",
            "shared/first-pass-blueprint.mdc",
            "create/first-submit-acceptance-gate.mdc",
            "shared/dockerfile.mdc",
            "shared/runtime-verifier.mdc",
            "verify/pre-zip-audit.mdc",
        ],
    ),
    "ENGINE_5_verify.mdc": (
        "ENGINE_5 — VERIFY",
        "Oracle/NOP, pre-zip audit",
        SHARED_CORE
        + [
            "verify/VERIFY-RULES.mdc",
            "verify/pre-zip-audit.mdc",
            "shared/first-pass-blueprint.mdc",
            "create/first-submit-acceptance-gate.mdc",
            "shared/runtime-verifier.mdc",
            "shared/canonical-base-image-gate.mdc",
            "shared/canonical-ecr-dockerfile-auto.mdc",
            "shared/difficulty-benchmark-models.mdc",
            "shared/platform-preferences.mdc",
            "revise/oracle-fix-g025-g027.mdc",
        ],
    ),
    "ENGINE_6_zip.mdc": (
        "ENGINE_6 — ZIP",
        "pack_zip.sh, flat root, gates",
        SHARED_CORE
        + [
            "zip/ZIP-RULES.mdc",
            "verify/VERIFY-RULES.mdc",
            "verify/pre-zip-audit.mdc",
            "create/first-submit-acceptance-gate.mdc",
            "revise/trivial-hardening-probes.mdc",
            "shared/anti-spam-templated-submissions.mdc",
            "revise/oracle-fix-g025-g027.mdc",
            "shared/canonical-ecr-dockerfile-auto.mdc",
            "shared/task-toml-subcategories-gate.mdc",
            "shared/task-toml-category-gate.mdc",
        ],
    ),
    "ENGINE_7_revise.mdc": (
        "ENGINE_7 — REVISE",
        "TRIVIAL/EASY/hard/oracle/reviewer fixes",
        SHARED_CORE
        + [
            "revise/REVISE-RULES.mdc",
            "revise/oracle-fix-g025-g027.mdc",
            "revise/platform-hardness-guards.mdc",
            "revise/hardness.mdc",
            "revise/trivial-easy-difficulty-prompt-lock.mdc",
            "revise/trivial-hardening-probes.mdc",
            "reviewer/REVIEWER-RULES.mdc",
            "reviewer/reviewer-checklist.mdc",
            "reviewer/common-errors-reference.mdc",
            "shared/anti-trivial.mdc",
            "shared/first-pass-blueprint.mdc",
            "shared/difficulty-benchmark-models.mdc",
            "shared/platform-preferences.mdc",
            "shared/runtime-verifier.mdc",
            "shared/anti-spam-templated-submissions.mdc",
            "verify/VERIFY-RULES.mdc",
            "zip/ZIP-RULES.mdc",
        ],
    ),
}

ENGINE_TO_FILE = {
    "ENGINE_1": "ENGINE_1_ideas.mdc",
    "ENGINE_2": "ENGINE_2_anti_spam.mdc",
    "ENGINE_3": "ENGINE_3_create.mdc",
    "ENGINE_4": "ENGINE_4_audit.mdc",
    "ENGINE_5": "ENGINE_5_verify.mdc",
    "ENGINE_6": "ENGINE_6_zip.mdc",
    "ENGINE_7": "ENGINE_7_revise.mdc",
}


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip("\n")
    return text


def _read_source(rel: str) -> str:
    path = ARCHIVE / rel
    if not path.is_file():
        raise FileNotFoundError(f"Missing archive source: {rel}")
    return _strip_frontmatter(path.read_text(encoding="utf-8"))


def build_bundle(filename: str, title: str, desc: str, sources: list[str]) -> str:
    seen: set[str] = set()
    parts: list[str] = [
        "---",
        f"description: Terminus {title} — full verbatim policy (alwaysApply false; hook loads one)",
        "alwaysApply: false",
        "---",
        "",
        f"# {title}",
        "",
        desc,
        "",
        "> Built by `scripts/build_consolidated_rules.py` from `archive/terminus-rules-mdc/`.",
        "> Re-run script after editing archive sources.",
        "",
    ]
    for rel in sources:
        if rel in seen:
            continue
        seen.add(rel)
        body = _read_source(rel)
        parts.extend(
            [
                "",
                "---",
                "",
                f"<!-- SOURCE: {rel} -->",
                "",
                body,
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    if not ARCHIVE.is_dir():
        print(f"ERROR: {ARCHIVE} not found")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for fname, (title, desc, sources) in BUNDLES.items():
        out_path = OUT / fname
        text = build_bundle(fname, title, desc, sources)
        out_path.write_text(text, encoding="utf-8")
        kb = len(text.encode("utf-8")) // 1024
        print(f"Wrote {out_path.relative_to(REPO)} ({kb} KiB, {len(sources)} sources)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
