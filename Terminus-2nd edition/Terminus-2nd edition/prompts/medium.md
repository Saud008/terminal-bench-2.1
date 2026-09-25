# Terminus — MEDIUM difficulty prompts

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


Use when platform shows **`difficulty = medium`** — **not** TRIVIAL/EASY (→ `trivial.md`) and **not** HARD unsolvable (→ `hard.md`).

**Benchmark agents (LOCKED):** Parse **`terminus-claude-opus-4-8`** and **`terminus-gpt5-5`** lines in Agent Performance (not legacy Opus 4.6 / GPT-5.2).

**Load with:** `shared/task-lifecycle.mdc` (Phase D), **@REVISE RULES**, `shared/anti-trivial.mdc`, **@REVIEWER RULES**, `shared/runtime-verifier.mdc`.

**Paths:** `tasks/<name>/` → `./scripts/pack_zip.sh <name>` → `tasksubmit/<name>.zip`

---

## Pick the right case

| Platform pattern | Example | Case | File |
|------------------|---------|------|------|
| **MEDIUM ✅** but **not solvable** — **≥1 test 0% forever** | Opus 4.8 **5/5**, GPT-5.5 **3/5**, some tests **0/N** | **Case 1** | [`medium-case-1.md`](medium-case-1.md) |
| **MEDIUM ✅** and **solvable** — want **harder** (~**1/5** worst model) | either agent **~3/5**, all tests pass sometimes | **Case 2** | [`medium-case-2.md`](medium-case-2.md) |
| Unsolvable + unclear root cause / harness | Mixed signals, oracle issues | **Case 3** | [`medium-case-3.md`](medium-case-3.md) |

### Quick routing

```
IF any test = 0% forever (0 passed / N runs for ALL agents)
  → Case 1 FIRST (fix fairness — NOT hardening)

IF status = solvable AND worst model ~40–60% (e.g. 3/5) AND user wants ~1/5 pass rate
  → Case 2 (harden to HARD band)

IF verifier_did_not_run OR oracle 0%
  → revise/oracle-fix-g025-g027.mdc + runtime-verifier FIRST (not a medium case)

IF difficulty = HARD (not medium)
  → prompts/hard.md instead
```

**Do not** run Case 2 (hardening) while **any** test is 0%-forever — fix solvability first (Case 1).

---

## Shared constraints (all cases)

- `instruction.md`: ≤3 short paragraphs, absolute paths, no solution hints
- `task.toml`: `allow_internet = false`, `workdir = "/app"`
- `tests/test.sh`: no runtime installs; Harbor reward block at end
- Verifier deps in Dockerfile only
- Oracle **1**, NOP **0** before resubmit
- Triage reviewer feedback: **@REVIEWER RULES** — do not trivialize

---

## Auto-route from platform summary

1. Parse **`terminus-claude-opus-4-8` X/5**, **`terminus-gpt5-5` Y/5** full-suite pass rates.
2. Mark tests with **0 passed / N runs** as **0%-forever**.
3. Pick case from table above.
4. Load chosen `medium-case-*.md` **in full** before edits.

---

## Invoke

```text
@prompts/medium.md
Fix tasks/<task-name> — MEDIUM platform summary below.

Platform summary:
<paste Difficulty, Status, Agent Performance, Unit Tests Results>
```

```text
@prompts/medium.md — Case 2
Harden tasks/<task-name> to ~1/5 worst model per medium-case-2.md
```
