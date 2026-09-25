# HARD Case 2 — Controlled ease (0/5 → target 1–2/5)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Platform shows **HARD ✅** but **`terminus-claude-opus-4-8` 0/5 and `terminus-gpt5-5` 0/5** on the **full suite**. Tests are **not** clearly broken (no single 0%-forever unfair test — if there is, use **Case 1** first). Goal: make the task **slightly** easier so **~1–2 out of 5** agent runs pass, without becoming TRIVIAL/EASY (>60% worst model).

---

## Platform evidence (paste below)

**Task:**

**Summary:**

**Artifacts:**

**Current agent performance:** `terminus-claude-opus-4-8` **0/5**, `terminus-gpt5-5` **0/5** (or equivalent full-reward counts)

**Target after repair:**

- **Solvable:** at least one strong agent passes **all** tests
- **Pass band:** worst model **~20–40%** (1–2/5), **not** >60%
- Keep `difficulty = hard` unless platform forces relabel after new eval
- **Controlled ease only** — replace selected **hard** tests with **medium** equivalents

---

## Step 1 — Inspect before editing (mandatory)

List task tree. Read instruction, docs, tests, environment, oracle.

Build test difficulty table:

| Test | Pass rate | Semantic depth | Candidate to ease? |
|------|-----------|------------------|-------------------|
| … | … | hard / medium | only if 0% all runs AND not core anti-cheat |

**Rules for picking tests to ease:**

- **Keep** tests that encode core contract (replay, checksum, idempotency, cross-module bugs)
- **Keep** tests some partial runs almost pass (agents fail for real semantic reasons)
- **Replace** only tests that block all agents despite fair docs + working oracle
- Swap **hard → medium**: same **family** of behavior, fewer interacting edge cases or one less trap layer — **not** grep-only or golden-dict checks

**Do not start editing until this table is done.**

---

## Step 2 — Controlled test replacement

1. Identify **2–4** hard tests to replace (not delete without replacement)
2. Each replacement must:
   - Still run real CLI/API/service paths
   - Still use independent reference or behavioral assertion
   - Be documented in instruction or `/app/docs/`
   - Be **strictly easier** than the removed test (one fewer trap, clearer contract, smaller fixture)
3. **Do not** remove:
   - Independent `reference_*` recomputation
   - Rebuild/subprocess gates
   - Anti-cheat mutated fixtures (unless proven unfair)

**Do not:**

- Drop test count below meaningful coverage
- Remove all cross-module or stateful checks
- Change oracle to write golden files only
- Lower `difficulty` in `task.toml` preemptively

---

## Step 3 — Align docs if eased behavior is documented elsewhere

If eased tests check behavior already in docs but agents miss due to test stacking, you may **narrow** test scope — do **not** add new hints to `instruction.md`.

---

## Step 4 — Repo constraints

Same as `hard.md` shared constraints. Oracle must pass new medium tests. NOP must still fail on broken env.

---

## Step 5 — Verify locally (mandatory)

1. Docker build  
2. Oracle → **1.0** on full suite (including new medium tests)  
3. NOP → **0.0**  
4. Confirm broken starter still fails majority of original hard behaviors

---

## Step 6 — Output

- Which hard tests were replaced and what medium tests replaced them
- Why each swap preserves HARD intent
- Files changed
- Oracle / NOP results
- **Solvable: yes/no**
- **Expected pass band:** ~1–2/5 (confirm after new platform eval)
