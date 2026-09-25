# HARD Case 3 — Full unsolvable diagnosis + fair repair

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Task marked **not solvable**; you need a **complete, evidence-based** repair. Use when the summary does not clearly fit Case 1 (isolated 0%-forever tests) or Case 2 (blanket 0/5 ease). Preserves intended difficulty **as much as possible** while making the task **fair and solvable**.

---

## Platform evidence (paste below)

**Task:**

**Summary:**

**Artifacts:** (benchmark, failed tests, agent logs, oracle/NOP logs)

**Current agent performance:**

**Problem:** Status = not solvable (at least one test 0% forever, or verifier/oracle mismatch)

**Benchmark agents (LOCKED):** Quote **`terminus-claude-opus-4-8`** and **`terminus-gpt5-5`** from Agent Performance. Apply **`prompts/hard.md` § Solvable ≠ Trivial** when fixing spec gaps — do not drop hard tests or add solution hints.

---

## Step 1 — Inspect before editing (mandatory)

Read **actual files** — do not guess:

- `instruction.md`, `task.toml`, `environment/Dockerfile`, `tests/test.sh`, `tests/test_outputs.py`
- `/app/docs/` contracts in `environment/docs/`
- `solution/solve.sh` and oracle sources
- `rubric.md` if present (platform rubric elsewhere — do not add to zip unless asked)
- Platform artifacts: per-test pass rates, agent trajectories, verifier stdout

Build:

| Test | `terminus-claude-opus-4-8` | `terminus-gpt5-5` | All agents | Root cause hypothesis |
|------|--------|-----|------------|------------------------|
| … | | | | |

Also check **non-test blockers:**

| Check | Evidence | Fix if broken |
|-------|----------|---------------|
| `verifier_did_not_run` | reward/CTRF missing | `test.sh` early reward, `cd /app`, no pre-pytest exit |
| Oracle fail | platform oracle 0 | real `solve.sh` patches + rebuild |
| Hidden requirements | test asserts undoc behavior | docs or instruction alignment |
| Agent-visible leaks | BUG comments, anti-cheat README | remove/neutralize |
| Tests in image | `environment/` has verifier files | move to `tests/` / build-time only |

**Do not start editing until tables are done.**

---

## Step 2 — Fix root cause (priority order)

1. Align instructions/docs with tested behavior  
2. Fix broken or unfair verifier expectations  
3. Fix path, CLI, fixture, ordering, or environment mismatches  
4. Fix `tests/test.sh` if verifier exits before pytest or skips reward/CTRF  
5. Update oracle only if it does not satisfy the same documented contract  
6. Replace impossible tests with equivalent fair behavior tests  
7. Ease a test only if proven impossible or hidden after alignment  

**Do not** remove hard tests just to increase pass rate.

**Preserve** where possible:

- State, replay, persistence, ordering, rollback, recovery  
- Malformed input handling, checksums, cross-module behavior  
- Tests that **some** agents already pass or fail for real semantic reasons  

---

## Step 3 — Terminus compliance checklist

- `[environment] allow_internet = false`
- No runtime dependency installs in `tests/test.sh`
- Verifier dependencies preinstalled in Dockerfile (`requirements.lock` + hashes when using pip)
- No tests, solution, hidden fixtures, expected outputs, or verifier-only files in agent image
- No grading/verifier/pytest/hidden-test wording in agent-visible docs
- No bug-revealing comments or solution hints in `environment/`
- Oracle fixes real source; passes same verifier as agents
- NOP fails on broken starter
- `tests/test.sh`: `mkdir -p /logs/verifier`, initial reward `0`, CTRF bootstrap, explicit `cd /app`

---

## Step 4 — Verify locally (mandatory)

1. Docker build  
2. Oracle + verifier offline → reward **1**  
3. NOP → reward **0**  
4. Static checks / ruff if available  
5. Collapse check if available  

---

## Step 5 — Output

- Which tests made the task unsolvable  
- Exact root cause for each  
- Exact files changed (minimal list)  
- Oracle result  
- NOP result  
- **Solvable: yes/no**  
- **Difficulty preserved: yes/no** — and what was intentionally eased (if anything)  

**Goal:** solvable by at least one strong agent without TRIVIAL/EASY drift.
