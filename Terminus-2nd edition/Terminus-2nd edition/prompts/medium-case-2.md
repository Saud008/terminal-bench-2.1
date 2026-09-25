# MEDIUM Case 2 — Harden solvable MEDIUM → ~1/5 (upgrade to HARD)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Platform shows **MEDIUM ✅** and task is **solvable** (≥1 agent passes full suite). Worst model is **too high** (e.g. `terminus-claude-opus-4-8` **5/5**, `terminus-gpt5-5` **3/5** ~60%) and user wants **~1/5** pass rate on the weaker model — **upgrade to HARD band**.

**Prerequisites:**

- **No** test at **0% forever** — if any exist, use **`medium-case-1.md` first**
- Oracle **1**, NOP **0** locally before hardening
- User explicitly wants harder task (not accidental Easy drift fix)

---

## Platform evidence (paste below)

**Task:**

**Summary:**

**Current agent performance:** e.g. `terminus-claude-opus-4-8` **5/5**, `terminus-gpt5-5` **3/5**

**Goal:** Target **~1/5** (~20%) on worst model — **HARD** band, not MEDIUM/Easy.

---

## Step 1 — Inspect (mandatory)

List task tree. Read instruction, docs, tests, environment, oracle.

| Test | Pass rate all agents | Depth | Harden candidate? |
|------|----------------------|-------|-------------------|
| … | … | shallow / medium / hard | replace only if **10/10** pass |

**Keep** tests that already separate strong vs weak agents fairly.  
**Replace or extend** tests that **every** agent passes — add behavioral depth, not grep-only.

---

## Step 2 — Hardening strategy (fair)

1. **Replace 3–6** “everyone passes” tests with **harder behavioral** checks:
   - Independent reference recomputation (not golden dict)
   - Replay / idempotency / epoch or inode invalidation
   - Hidden fixture mutation (anti-cheat)
   - Cross-module interaction (≥2 subsystems must be correct)
2. Add **interacting bugs** in environment if needed (≥4 across 3+ modules) — update oracle with real fixes
3. Align new behavior in **`/app/docs/`** + brief `instruction.md` — **no hidden test-only rules**
4. Set `difficulty = hard` in `task.toml` after hardening (target band)

**Do not:**

- Add 20 tests or remove all GPT-failing tests (creates Easy)
- Use latency thresholds or hardware-dependent flakes
- Weaken oracle to skip new tests
- Copy tests from another task in the same family

---

## Step 3 — Preserve solvability

- Oracle must pass **all** new tests offline (G-025)
- One shallow patch must **not** pass full suite
- Instruction stays ≤3 paragraphs; contracts in `/app/docs/`

---

## Step 4 — Verify

1. Docker build  
2. Oracle → reward **1** (all tests)  
3. NOP → reward **0**  
4. Optional: local agent smoke — expect worst model **~1/5**, not 0/5

---

## Step 5 — Output

- Which tests replaced/added and why
- New difficulty target (**hard**, ~1/5 worst model — **planned** until platform re-eval)
- Files changed
- Oracle changes
- **Solvable: yes** (must remain yes)
- **Do not** claim 1/5 pass rate without new agent eval evidence
