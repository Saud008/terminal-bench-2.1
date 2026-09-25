# Terminus — HARD difficulty / unsolvable repair prompts

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


Use when the platform shows **difficulty = hard** (or medium/hard) but **status = not solvable** / unfair tests — **not** when agents pass too easily.

**TRIVIAL / EASY** (agents 4/5–5/5) → **`prompts/trivial.md`** instead.

**Load with:** `shared/task-lifecycle.mdc` (Phase D), `shared/task-lifecycle.mdc` §2, `shared/anti-trivial.mdc`, `reviewer/REVIEWER-RULES.mdc`, `shared/runtime-verifier.mdc`.

**Paths:** edit in place — `tasks/<name>/` → `./scripts/pack_zip.sh <name>` → `tasksubmit/<name>.zip` (see `shared/repo-workflow.mdc`).

---

## Pick the right case from platform summary

Read the agent benchmark table (per-test pass rates, **`terminus-claude-opus-4-8`** vs **`terminus-gpt5-5`**). Then open **one** case file below.

| Platform pattern | Example | Case | File |
|------------------|---------|------|------|
| **HARD ✅** but **not solvable** — some agents pass many tests; **≥1 test 0% forever** | Opus 4.8 **0/5**, GPT-5.5 **3/5** | **Case 1** | [`hard-case-1.md`](hard-case-1.md) |
| **HARD ✅** but **everyone fails full suite** — fair task, too hard; ease to **~1–2/5** | Opus 4.8 **0/5**, GPT-5.5 **0/5** | **Case 2** | [`hard-case-2.md`](hard-case-2.md) |
| **Unsolvable** — need full audit (logs, oracle, NOP, harness, docs); fix root cause only | Any 0%-forever test; unclear cause | **Case 3** | [`hard-case-3.md`](hard-case-3.md) |

### Quick routing

```
IF any test = 0% forever AND other tests pass sometimes
  → Case 1 (fix 0%-forever tests only; keep HARD)

IF all agents 0/5 on full suite AND no single test is clearly broken
  → Case 2 (controlled ease: swap some hard tests for medium; target 1–2/5)

IF status = unsolvable AND you need full audit (logs, oracle, NOP, docs, harness)
  → Case 3 (full diagnosis + minimal fair fix)
```

**Do not** use Case 2 when Case 1 applies (fix unfair tests first).  
**Do not** use Case 2 or 3 to remove most hard tests — that creates **TRIVIAL/EASY** (>60% worst-model pass).

---

## Solvable ≠ Trivial (LOCKED — read before any edit)

Platform difficulty uses benchmark agents **`terminus-claude-opus-4-8`** and **`terminus-gpt5-5`**. `@prompts/hard.md` fixes **fairness** so at least one run can pass **all** tests — it does **not** license making the task **EASY/TRIVIAL** (worst model **>60%**).

### Parse the pasted summary exactly

Before choosing a case, quote from the user’s platform block:

1. **Agent Performance** — `terminus-claude-opus-4-8` X/N, `terminus-gpt5-5` Y/N full reward (not partial pytest counts alone).
2. **Unit Tests Results** — which tests are **0/N forever** vs **sometimes pass**.
3. **Analysis on Agent Failures** — root cause (spec gap, harness, too hard, etc.).

Route from **those facts**, not from “agents scored 0” alone. Example: Claude **0/5**, GPT **0/5**, but **13/14** per-test passes and one test **0/10** with “instruction sufficiency FAIL” → **Case 1** (spec alignment only), **not** Case 2 blanket ease.

### Allowed Case 1 fixes (fairness only)

- Document a behavior the test already asserts but `instruction.md` / `/app/docs/` omit (exact error strings, staging schema, format).
- Fix broken or flaky tests; fix oracle/harness; fix environment bugs blocking a fair contract.

### Forbidden “solvability” moves (make task trivial)

- Drop or weaken hidden tests, anti-cheat traps, or staging/idempotency checks because agents struggle elsewhere.
- Add bug file names, fix order, operators, or golden outputs to `instruction.md` or `environment/`.
- Replace behavioral tests with grep-only or static golden dicts.
- Use Case 1 when the real issue is **both models ≥3/5** — that is **`@prompts/trivial.md` / Case 6**, not hard Case 1.

### After a Case 1 (or 3) fix — difficulty recheck (mandatory before zip)

1. Oracle **1.0**, NOP **0.0** (same verifier as agents).
2. Paste **`revise/trivial-hardening-probes.mdc`** table — probes **1, 1b, 7, 8** minimum; any **FAIL** → no zip.
3. If summary showed **high partial pass** (e.g. 13/14 tests, 9/10 on most tests) before the fix, **predict** post-fix benchmark: if either model would likely hit **≥3/5**, tell the user and apply **`@prompts/trivial.md` Case 6** in the same revision **or** stop and ask — do **not** ship a fairness-only patch that turns a HARD task into EASY/TRIVIAL without saying so.
4. **Solvable** = fair + at least one agent *can* pass all tests. **HARD** = confirmed only after **new** platform eval (worst model **≤~20%** is OK; Claude **0/5** on a fair task is valid per `shared/platform-preferences.mdc` §1b).

**Case 2** is controlled ease when **all agents 0/5 on the full suite** and tests are fair — target **~1–2/5**, not 5/5. Never ease to lift pass rate when the blocker was an undocumented test-only rule.

---

## Shared constraints (all cases)

- `instruction.md`: ≤3 short paragraphs, absolute paths, no solution hints
- `task.toml`: `allow_internet = false`, `workdir = "/app"` (non-milestone)
- `tests/test.sh`: no runtime installs; reward `0`/`1` block at end; `cd /app`; early CTRF + reward `0` to avoid `verifier_did_not_run`
- Verifier deps in `environment/Dockerfile` only; no tests/solution in agent image
- No `rubric.md` in zip unless explicitly requested
- Oracle must pass **same** verifier as agents; NOP must fail
- **Verified by execution** — oracle 1.0 + NOP 0.0 before resubmit

---

## Auto-route from platform summary (mandatory)

When user pastes a **Difficulty / Status / Agent Performance / Unit Tests Results** block:

### Step A — Parse summary

1. **Full-suite pass rate:** `terminus-claude-opus-4-8` X/5, `terminus-gpt5-5` Y/5 (any run with reward 1 = pass).
2. **Per-test table:** mark tests with **0 passed / N runs** as **0%-forever**.
3. **Oracle / NOP:** oracle must be 100%; NOP must be 0%.

### Step B — Pick case

| Condition | Case | Prompt file |
|-----------|------|-------------|
| **≥1 test at 0/N** AND **≥1 other test passes sometimes** (any agent) | **Case 1** | `prompts/hard-case-1.md` |
| **`terminus-claude-opus-4-8` 0/5 AND `terminus-gpt5-5` 0/5** on full suite AND tests are not clearly broken/unfair | **Case 2** | `prompts/hard-case-2.md` |
| Opus 4.8 **0/5**, GPT-5.5 **3/5** (or mixed) with **0%-forever tests** | **Case 1** (not Case 2) | `prompts/hard-case-1.md` |
| Unsolvable + need harness/oracle/docs audit OR mixed signals | **Case 3** | `prompts/hard-case-3.md` |
| **verifier_did_not_run** or oracle 0% | **Not a hard case** | `shared/runtime-verifier.mdc` + oracle G-025–G-027 first |

**Rule:** If **any** test is 0%-forever → **Case 1 or 3 first**, never Case 2 until fairness is fixed.

### Step C — Execute

Load the chosen `hard-case-*.md` **in full** and follow every step. Do not skip the per-test triage table.

---

## How to invoke in chat

```text
@prompts/hard.md
Fix tasks/<task-name> — apply HARD case per platform summary below.

Platform summary:
<paste Difficulty, Status, Agent Performance, Unit Tests Results>
```

Agent must: (1) quote summary facts (`terminus-claude-opus-4-8` / `terminus-gpt5-5` runs, 0%-forever tests, analysis root cause), (2) route to Case 1/2/3 using table above, (3) build per-test triage table before edits, (4) apply **Solvable ≠ Trivial** guardrails, (5) oracle + NOP + probe table after fixes, (6) flag if fairness fix likely pushes either benchmark **≥3/5** (Case 6 may be needed).

### Explicit case override

```text
@prompts/hard.md — Case 1
Fix tasks/<task-name> per prompts/hard-case-1.md
```
