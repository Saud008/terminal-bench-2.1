# TRIVIAL Case 2 — Still too easy; deepen behavior (not shallow edge cases)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When:** Task remains **trivial/easy** but agents are not necessarily **5/5** — needs deeper engineering, not more simple edge cases.

**Target:** ~20% worst-model pass; best model occasionally passes — **not unsolvable**.

**Also load:** [`trivial-repo-wide.md`](trivial-repo-wide.md) — repository-wide contract (§1–§12).

---

## Platform evidence (paste below)

```
[paste agent results, which tests are consistently solved]
```

---

## Step 1 — Identify easy wins for agents

From artifacts, list tests with **high pass rate** → **replace or strengthen**.

Keep tests that already catch **meaningful semantic failures**.

---

## Step 2 — Add harder fair behavior

Where domain fits, add coverage for:

- Interacting logic and **state changes**
- **Persistence** and **stale-state recovery**
- **Ordering** and merge semantics
- **Replay / idempotency** across runs
- **Rollback** on invalid input
- **Malformed / partial corrupt** inputs
- **Cross-module dependencies** (fix in A breaks B until both fixed)

**Do not add:** hidden requirements, vague wording, brittle formatting, source-grep-only, hardcoded expected outputs.

---

## Step 3 — Block shallow passes

Task must **not** be passable with:

- One-line fix  
- Single obvious file edit  
- Stubbed API/CLI response  
- Direct artifact generation  

---

## Step 4 — Verify

Oracle, NOP, static checks. Confirm verifier stable.

**Do not resubmit** until oracle passes, NOP fails, and design plausibly breaks strong agents for **implementation** reasons.

---

## Output

- Tests replaced vs kept  
- New behaviors added (and where documented in contract docs)  
- Commands + results  
