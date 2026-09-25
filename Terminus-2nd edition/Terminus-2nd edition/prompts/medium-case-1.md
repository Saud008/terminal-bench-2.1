# MEDIUM Case 1 — Solvability repair (0%-forever tests)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Difficulty **MEDIUM ✅** is fine. **Status: not solvable** because **≥1 verifier test has 0% pass rate across all agent runs** — even if `terminus-claude-opus-4-8` passes the full suite (e.g. **5/5**) and `terminus-gpt5-5` is partial (e.g. **3/5**).

**This is not a hardening task until status is green.**

---

## Platform evidence (paste below)

**Task:**

**Summary:**

**Artifacts:**

**Current agent performance:** e.g. `terminus-claude-opus-4-8` **5/5**, `terminus-gpt5-5` **3/5**

**Problem:** Some tests have **0% pass rate across all agent runs** — blocks solvable status.

**Target after repair:**

- **Solvable:** ≥1 full agent run passes **all** tests
- Stay **MEDIUM:** worst model **>20% and ≤60%** (~2–3/5) — do **not** push to 5/5 (Easy) or 0/5 (broken)
- **Do not** optimize for “only 1/5” unless user explicitly asks for HARD (→ `medium-case-2.md` after solvable)

---

## Step 1 — Inspect and classify (mandatory)

List task tree. Read `instruction.md`, `/app/docs/`, `tests/test_outputs.py`, `environment/`, `solution/`.

| Category | Action |
|----------|--------|
| **0% every agent, every run** | **Priority fix** — alignment, broken test, oracle gap |
| **Passed by Claude, failed by GPT** | Usually **fair hard** — keep; optional doc clarity only |
| **Passed by all agents** | Keep for now; optional small hardening **after** solvable (Case 2) |

Per-test table:

| Test | Pass rate | Opus 4.8 | GPT-5.5 | Action |
|------|-----------|----------|---------|--------|
| … | … | … | … | fix / keep |

Identify **why** 0%-forever tests fail: spec contradiction, hidden requirement, broken test, oracle gap, environment bug, flake.

**Do not edit until this table is done.**

---

## Step 2 — Fix 0%-forever tests first (minimal)

Same order as HARD Case 1:

1. Instruction ↔ test alignment (`/app/docs/` + `instruction.md`)
2. Fix broken tests (wrong expected values, paths, flake)
3. Fix environment if contract is correct but app cannot satisfy
4. Update oracle (real fixes, offline — G-025)
5. Replace only **unfair** tests with equivalent behavioral checks
6. Ease only if proven impossible after alignment — smallest change

**Do not:**

- Remove hard tests to get solvable while staying unfair elsewhere
- Harden while 0%-forever tests still exist
- Break oracle/NOP gates

---

## Step 3 — Optional MEDIUM tuning (only after solvable)

**Only if** after Step 2 platform would rate **Easy** (worst **>60%**, e.g. Claude 5/5 + trivial tests):

- Harden **2–5 tests** that **all** agents pass (replay, idempotency, cross-module) — same domain, no new hidden rules
- Trim hints in `instruction.md` (≤3 paragraphs)

If worst model is already **~60%** (3/5), **stop after solvability** unless user asks for HARD (→ `medium-case-2.md`).

---

## Step 4 — Avoid

- Making Claude drop to 0% with unfair tests
- Hardening while 0%-forever tests still exist
- TRIVIAL/Easy drift (worst >60%)
- Impossible suite (0/5 all agents)

---

## Step 5 — Repo constraints + verify

- `tests/test.sh`: bootstrap `/logs/verifier`, reward `0`/`1`, no runtime installs
- Oracle **1**, NOP **0** on **every** test including former 0%-forever
- Repack `tasksubmit/<name>.zip` (G-026, G-027)

---

## Step 6 — Output

- 0%-forever tests: root cause + exact fix per test
- Optional hardening (if any) and why
- Files changed (minimal)
- Oracle changes
- Commands and results
- **Solvable: yes/no**
- **Difficulty: target MEDIUM** — confirm only after **new** agent eval

Do not claim fixed until oracle passes **every** test.
