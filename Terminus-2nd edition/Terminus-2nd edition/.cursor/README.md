# .cursor — Terminus (aligned layout)

```
User message
    → hooks/route-terminus-prompt.py
    → scripts/terminus_rules_engine.py
    → injects ONE of .cursor/rules/engines/ENGINE_*.mdc (full verbatim rules)
```

## Always on (small — do not duplicate elsewhere)

| File | Role |
|------|------|
| `rules/terminus.mdc` | Hub — ENGINE map, standing defaults |
| `rules/sanjana-standing-requirements.mdc` | **LOCKED** — full pipeline, no permission asks |
| `rules/shared/*.mdc` | **7 lock files** — trivial/EASY block, rubric path, jobs-local, workflow automation |
| `rules/create/first-submit-acceptance-gate.mdc` | Phase F′ before first zip |

## One ENGINE per turn (hook injects)

| ENGINE | Phase |
|--------|-------|
| `ENGINE_1_ideas.mdc` | Ideas |
| `ENGINE_2_anti_spam.mdc` | Anti-spam |
| `ENGINE_3_create.mdc` | CREATE A→H |
| `ENGINE_4_audit.mdc` | Audit |
| `ENGINE_5_verify.mdc` | Verify |
| `ENGINE_6_zip.mdc` | Zip |
| `ENGINE_7_revise.mdc` | Revise / TRIVIAL |

**Source of truth:** edit `archive/terminus-rules-mdc/` → `python3 scripts/build_consolidated_rules.py`

**Sync live locks → archive** after editing `.cursor/rules/shared/` or `sanjana-standing-requirements.mdc`:

```bash
for f in block-trivial-platform-acceptance no-easy-upload-lock trivial-first-upload-lock \
  jobs-local-layout-lock rubric-storage-lock workflow-prompt-automation-lock \
  trivial-fix-invoke-mandatory-steps; do
  cp ".cursor/rules/shared/$f.mdc" "archive/terminus-rules-mdc/shared/$f.mdc"
done
cp .cursor/rules/sanjana-standing-requirements.mdc archive/terminus-rules-mdc/shared/
python3 scripts/build_consolidated_rules.py
```

## Prompts (canonical — repo root)

| Use | Path |
|-----|------|
| **Read / fix** | `prompts/*.md` only (e.g. `trivial.md`, `trivial-case-6.md`, `trivial-fix-invoke.md`) |
| **@ tag hints** | `archive/terminus-rules-mdc/prompts/*.mdc` + `tag-prompts/*.mdc` (`alwaysApply: false`) |

**Removed:** `prompts/CURSOR-AT-TAG.md` — use [`prompts/HOW-TO-USE.md`](../prompts/HOW-TO-USE.md) instead.

## Pack gate chain (`pack_zip.sh`)

ECR → subcategories → category → anti-spam → unacceptable 8/8 → F′ → agent calibration → difficulty design → **trivial shape** → CI → verify

**Healthcheck:** `python3 scripts/terminus_engine_healthcheck.py`

Restart Cursor after hook or ENGINE bundle changes.
