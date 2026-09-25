# LOCKED — Prompts policy

**All files in `prompts/` are LOCKED canonical copy-paste prompts.** Do not improvise workflow paths or weaken difficulty unless the user explicitly overrides in the current message.

**Main hub:** `.cursor/rules/shared/WORKFLOW-MAP.mdc` (all `.mdc` rules `alwaysApply: true`)  
**Rules index:** `.cursor/rules/LOCKED.mdc`  
**Pack zips:** `./scripts/pack_zip.sh <name>` only — never manual `zip -r` for upload

**User chooses:** (1) **@ tag one** prompt rule + summary, or (2) **automated** — summary + task path only. Both → analyze → router → best case. One clarifying question if summary missing (no guessing).

**Ask, don't hallucinate:** no fake platform scores, no invented reviewer text, no "verified" without oracle/NOP runs.

---

## Benchmark agents (Jun 2026 — LOCKED)

Platform **Difficulty / Status / Agent Performance / Unit Tests** summaries refer to:

| Model | Platform agent ID | Harbor slug (local smoke) |
|-------|-------------------|---------------------------|
| **Claude Opus 4.8** | `terminus-claude-opus-4-8` | `anthropic/@anthropic/claude-opus-4-8` |
| **GPT-5.5** | `terminus-gpt5-5` | `openai/@openai/gpt-5.5` |

**Supersedes:** Opus 4.6, GPT-5.2, Sonnet 4.5, Codex — **thresholds unchanged** (worst ≤~20% = HARD band; >60% = Trivial/Easy), but **pass rates are higher** on the same task.

**Design target:** **`terminus-claude-opus-4-8`** first — Claude **0/5** or timeout @ **1800s** on a fair task is valid HARD (`shared/platform-preferences.mdc` §1b). Do **not** chase GPT-5.5 off 5/5 with unfair spec gaps.

**Routing:** either model **≥3/5** → `@prompts/easy.md` / `trivial-case-6.md`; 0%-forever one test + high partial pass → `@prompts/hard.md` Case 1 (**Solvable ≠ Trivial**).

---

## Paths (LOCKED)

| Edit | Output |
|------|--------|
| `tasks/<name>/` | `tasksubmit/<name>.zip` |

Scan duplicates: `tasks/`, `tasks/_accepted-tasks/`, `tasksubmit/` only.

---

## Mandatory pairings (never use prompt alone)

| Prompt | Also load |
|--------|-----------|
| `newidea.md` | **@IDEAS RULES** |
| `audit.md` | **@AUDIT RULES** + **@REVIEWER RULES** + `reviewer-checklist.mdc` |
| `trivial.md` | **@REVISE RULES** + **`trivial-case-6.md`** + **`sp-hard-create-revise.md`** (`revise/trivial-easy-difficulty-prompt-lock.mdc`) |
| **`trivial-fix-invoke.md`** | **`shared/trivial-fix-invoke-mandatory-steps.mdc` (14 steps)** + trio above + **§3 fix prompt before edits** |
| `easy.md` | **@REVISE RULES** + `revise/hardness.mdc` + **`trivial-case-6.md`** + **`sp-hard-create-revise.md`** |
| `sp-hard-create-revise.md` | **@CREATE RULES** or **@REVISE RULES** + `trivial-case-6.md` + `trivial-repo-wide.md` + `revise/trivial-hardening-probes.mdc` + `platform-preferences.mdc` §1b–§1c |
| `medium.md` | **@REVISE RULES** |
| `hard.md` | **@REVISE RULES** |
| `reviewer.md` | **@REVIEWER RULES** |
| Oracle fail | `oracleFix.md` + **@REVISE RULES** (G-025–G-027) |
| Before upload | **@VERIFY RULES** then **@ZIP RULES** |

---

## Routers (auto-pick case file)

- `trivial.md` → `trivial-case-6.md` (default) + `trivial-case-1/2/audit/tb3` when summary matches
- `medium.md` → `medium-case-1.md` … `medium-case-3.md`
- `hard.md` → `hard-case-1.md` … `hard-case-3.md`
- `reviewer.md` → `reviewer-feedback-1.md` … `reviewer-feedback-6.md`

Full index: [`README.md`](README.md)
