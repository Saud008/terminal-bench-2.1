# HARD Case 1 — Solvability repair (0%-forever tests)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Difficulty **HARD ✅** is fine. At least one agent passes **some** tests, but **≥1 verifier test has 0% pass rate across all runs** — task is **not solvable** until those tests are fixed (unfair, broken, brittle, or misaligned). **Do not** blanket-remove hard tests.

---

## Platform evidence (paste below)

**Task:**

**Summary:**

**Artifacts:** (benchmark table, per-test pass rates, agent logs)

**Current agent performance:**

**Problem:** At least one verifier test has **never** been passed in any agent run.

**Target after repair:**

- **Solvable:** at least one benchmark run (`terminus-claude-opus-4-8` or `terminus-gpt5-5`) passes **all** tests on a **fair** contract
- Keep **HARD** band: worst model roughly **≤20%** (~1/5) after **new** eval is OK; Claude **0/5** on a fair task is valid
- **Do not** ease so much that worst model **>60%** (Trivial/Easy)
- **Minimal diff:** fix only what blocks 0%-forever tests

**Solvable ≠ Trivial (LOCKED):** Case 1 closes **spec/test fairness gaps** only. It is **not** permission to drop hidden tests, add solution hints, or weaken traps. If agents already pass **most** tests (e.g. 13/14) and only one test was 0% due to missing docs, fixing that doc may make **both** models pass often — before zip, run **`revise/trivial-hardening-probes.mdc`** (probes 1, 1b, 7, 8). If probes fail or you predict **≥3/5** on either model, route **`@prompts/trivial.md` Case 6** in the same pass or report to the user; do not silently trivialize.

---

## Step 1 — Inspect before editing (mandatory)

List the actual task tree. Read `instruction.md`, `/app/docs/` contracts, `tests/test_outputs.py`, `environment/`, oracle `solution/`.

From artifacts, build:

| Test (or group) | Pass rate all agents | Opus 4.8 | GPT-5.5 | Action |
|-----------------|----------------------|--------|-----|--------|
| 0% on every run | → **fix or replace** | | | |
| Passed by some runs | → **keep** | | | |

Identify **why** 0%-forever tests fail: hidden requirement, typo in test, wrong path, timing/flake, oracle doesn’t satisfy test, fixture mismatch, instruction omits rule, anti-cheat too strict, etc.

**Do not start editing until this table is done.**

---

## Step 2 — Fix root cause (not blanket easing)

Prefer in order:

1. **Instruction ↔ test alignment** — every asserted behavior in instruction or referenced `/app/docs/` schema
2. **Fix broken tests** — wrong expected values, wrong CLI flags, order-dependent flake, environment assumptions
3. **Fix environment bugs** if tests encode correct contract but app can never satisfy it
4. **Update oracle** so it passes the same contract agents must satisfy (real fixes, not skip tests)
5. **Replace only the offending tests** with equivalent **fair** behavioral checks — same intent, not weaker logic
6. **Ease only** tests proven impossible after alignment fix — smallest change

**Do not:**

- Remove most hard tests to get 2/5 passes (will become **TRIVIAL/EASY**)
- Add hidden requirements in tests only
- Weaken to static golden dicts or grep-only checks
- Break oracle or NOP gate

---

## Step 3 — Preserve HARD difficulty design

- Keep **4+ interacting bugs across 3+ modules** where possible
- Keep **independent reference recomputation**, checksums, replay/idempotency on tests agents *can* pass
- Claude may get **>0%** after fix — fine if worst model stays **≤~20–40%**; do not chase Claude 0% with unfair tests

---

## Step 4 — Repo constraints

- `tests/test.sh`: Harbor reward block at end; no runtime `pip`/`curl`/`apt`
- Verifier deps in Dockerfile; hidden fixtures under `/opt/verifier-fixtures/` or `tests/` only
- No bug-revealing comments in agent-visible source

---

## Step 5 — Verify locally (mandatory)

1. Docker build  
2. Oracle + verifier → reward **1** (every test, including former 0%-forever tests)  
3. NOP → reward **0**  
4. Optional: ruff / `run_static_checks.py`

---

## Step 6 — Output

- Quoted summary facts (`terminus-claude-opus-4-8` / `terminus-gpt5-5` full reward, 0%-forever test names, analysis root cause)
- Which tests were 0% forever and **exact fix** per test
- Files changed (minimal list)
- Oracle changes (if any)
- Commands and results
- **Trivial-hardening probe table** (probes 1, 1b, 7, 8) — PASS/FAIL per row
- **Solvable: yes/no** (target: yes)
- **Difficulty: target HARD** — confirm only after **new** agent eval (not from old 0/5 run alone)
- **Trivial risk:** if high partial pass before fix, state whether Case 6 hardening is needed before resubmit

Iterate until oracle passes all tests and design is **fair**, not until all models pass.
