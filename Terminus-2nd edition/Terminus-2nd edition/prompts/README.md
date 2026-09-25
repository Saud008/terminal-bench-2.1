# Terminus prompts (LOCKED)

> **You choose:** `@TRIVIAL PROMPT` / `@HARD PROMPT` / … **or** automated (summary only). See [`HOW-TO-USE.md`](HOW-TO-USE.md).

> **LOCKED** — Every file in `prompts/` is canonical. Policy: [`LOCKED.md`](LOCKED.md) · Hub: [`WORKFLOW-MAP.mdc`](../.cursor/rules/shared/WORKFLOW-MAP.mdc) · Pack: `./scripts/pack_zip.sh <name>`

**Benchmark agents (Jun 2026):** **`terminus-claude-opus-4-8`** (Claude Opus 4.8) + **`terminus-gpt5-5`** (GPT-5.5). Supersedes Opus 4.6 / GPT-5.2. Full table: [`LOCKED.md`](LOCKED.md) § Benchmark agents.

**Main hub:** `.cursor/rules/shared/WORKFLOW-MAP.mdc` (all `.mdc` rules `alwaysApply: true`) — links all `@` rule folders and this `prompts/` directory.

## NEW TASK IDEAS (Phase A — brainstorm only)

| File | Use when |
|------|----------|
| [`newidea.md`](newidea.md) | **Generate ideas** — Step 0 menu (counts or auto); default **25** non-milestone + **5** milestone; scan `tasks/` + `_accepted-tasks/` only |

```text
@prompts/newidea.md
```

Agent asks in English: how many non-milestone? how many milestone? Or auto (25+5).

```text
@prompts/newidea.md
non-milestone 10, milestone 2
```

Also: `@IDEAS RULES` → `.cursor/rules/ideas/IDEAS-RULES.mdc`

## AUDIT (post-creation — Phase C / pipeline Phase E)

| File | Use when |
|------|----------|
| [`audit.md`](audit.md) | **After creating** a new task — **always with** `@AUDIT RULES` + `@REVIEWER RULES` + full checklist (read-only) |

```text
@prompts/audit.md
@AUDIT RULES
@REVIEWER RULES

Audit tasks/<name> against Terminus rules.
Apply reviewer/reviewer-checklist.mdc in full. Do not modify files.
```

**Mandatory trio:** `audit.md` + `@AUDIT RULES` + `@REVIEWER RULES` + `reviewer-checklist.mdc`.

## TRIVIAL / EASY (agents pass too easily — Phase D)

| File | Use when |
|------|----------|
| [`easy.md`](easy.md) | **EASY** or either model **≥3/5** or worst **>40%** — **Case 6 only** |
| [`trivial.md`](trivial.md) | **Router** — TRIVIAL label; paste summary; **auto-pick** case (default **Case 6**) |
| [`trivial-case-1.md`](trivial-case-1.md) | Already flagged trivial — do not resubmit same form |
| [`trivial-case-2.md`](trivial-case-2.md) | Still easy — deepen behavior, not shallow edge cases |
| [`trivial-case-6.md`](trivial-case-6.md) | **Default** TRIVIAL/EASY — structural redesign (ingest→staging→export + decoy) |
| [`trivial-repo-wide.md`](trivial-repo-wide.md) | **Load with every edit case** — §1–§14 contract |
| `revise/trivial-hardening-probes.mdc` | **Before zip** — single-file / hidden / decorative probes |
| `revise/hardness.mdc` | **G-028–G-035** — staging, decoy, chained poison, new-model thresholds |
| [`trivial-case-audit.md`](trivial-case-audit.md) | **Audit only** — review + plan, no edits |
| [`trivial-tb3-hardening.md`](trivial-tb3-hardening.md) | TB3 rebuild + verifier stability + language migration |

```text
@prompts/trivial.md
Harden tasks/<name> — TRIVIAL/EASY on platform.

Platform summary:
[paste Difficulty, Status, Agent Performance, Unit Tests Results]
```

## SP HARD — create & revise (Claude-primary + repo-wide quality)

| File | Use when |
|------|----------|
| [`sp-hard-create-revise.md`](sp-hard-create-revise.md) | **New hard task** or **revise** — target **`terminus-claude-opus-4-8`** (0%/timeout @ 1800s OK); do **not** chase GPT-5.5 |

Combines: `platform-preferences.mdc` §1b + `trivial-case-6.md` + `trivial-repo-wide.md`.

**Claude strategy:** whole-task read → implement; hardness = multi-module scope + `/app/docs/` + stateful replay under **default 1800s agent timeout** (do not raise clock).

```text
@prompts/sp-hard-create-revise.md
CREATE tasks/<new-name>/
```

```text
@prompts/sp-hard-create-revise.md
REVISE tasks/<name>/
Platform summary: <paste>
```

## MEDIUM (difficulty in band but wrong status or too easy — Phase D)

| File | Use when |
|------|----------|
| [`medium.md`](medium.md) | **Router** — paste summary; auto-pick Case 1/2/3 |
| [`medium-case-1.md`](medium-case-1.md) | MEDIUM OK; **0%-forever tests** (e.g. Opus 4.8 **5/5**, GPT-5.5 **3/5**) — fix solvability first |
| [`medium-case-2.md`](medium-case-2.md) | **Solvable** MEDIUM; harden to **~1/5** worst model → HARD band |
| [`medium-case-3.md`](medium-case-3.md) | Full unsolvable audit (MEDIUM label) |

```text
@prompts/medium.md
Fix tasks/<name> — MEDIUM / unsolvable platform summary below.
```

```text
@prompts/medium.md — Case 2
Harden tasks/<name> to ~1/5 per medium-case-2.md
```

## HARD / unsolvable (difficulty OK but not solvable — Phase D)

| File | Use when |
|------|----------|
| [`hard.md`](hard.md) | **Router** — paste platform summary; auto-pick Case 1/2/3 |
| [`hard-case-1.md`](hard-case-1.md) | HARD OK; **0%-forever tests** (e.g. Opus 4.8 **0/5**, GPT-5.5 **3/5**) |
| [`hard-case-2.md`](hard-case-2.md) | Opus 4.8 **0/5 + GPT-5.5 0/5**; controlled ease → ~1–2/5 |
| [`hard-case-3.md`](hard-case-3.md) | Full unsolvable audit + fair repair |

```text
@prompts/hard.md
Fix tasks/<name> — unsolvable/unfair platform summary below.
```

## REVIEWER (line comments / NEEDS_REVISION — Phase D′)

| File | Use when |
|------|----------|
| [`reviewer.md`](reviewer.md) | **Router** — paste feedback; **auto-pick** RF1–RF6 (do not trivialize) |
| [`reviewer-feedback-1.md`](reviewer-feedback-1.md) | **RF1** — minimal fix: timeouts (600–900s), Linux user/password only |
| [`reviewer-feedback-2.md`](reviewer-feedback-2.md) | **RF2** — fix + oracle/NOP + static/quality until green |
| [`reviewer-feedback-3.md`](reviewer-feedback-3.md) | **RF3** — agent eval OK; preserve difficulty; minimal fix |
| [`reviewer-feedback-4.md`](reviewer-feedback-4.md) | **RF4** — full locked triage workflow (**default**) |
| [`reviewer-feedback-5.md`](reviewer-feedback-5.md) | **RF5** — standard fix + difficulty recheck |
| [`reviewer-feedback-6.md`](reviewer-feedback-6.md) | **RF6** — triage only + pushback message |

Also load: **@REVIEWER RULES** (`.cursor/rules/reviewer/REVIEWER-RULES.mdc`) + `shared/task-lifecycle.mdc` Phase D′.

```text
@prompts/reviewer.md
Fix tasks/<name> per reviewer feedback below.

Reviewer feedback:
[paste here]
```

---

## Removed (Jun 2026)

| File | Status |
|------|--------|
| `trivial-harden.md`, `trivial-case-4.md`, `trivial-case-5.md` | **Deleted** — route to **`trivial-case-6.md`** only |
| `CURSOR-AT-TAG.md` | **Removed** — use `HOW-TO-USE.md` |

**@ tag stubs** live in `archive/terminus-rules-mdc/prompts/*.mdc` and `tag-prompts/*.mdc` (optional hints; `alwaysApply: false`). Canonical text is always `prompts/*.md` at repo root.
