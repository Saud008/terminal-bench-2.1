# Reviewer feedback — RF3 (agent eval OK; minimal fix; preserve difficulty)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Task **rejected on review** but **agent eval is already acceptable** (difficulty + solvability OK). Apply reviewer updates **without changing difficulty**; oracle **1**, NOP **0**.

---

## Context

- Agent pass band is acceptable — **do not** re-harden or re-ease for agent stats unless a reviewer comment **explicitly** requires it.
- **Goal:** pass review with **minimal required changes** — avoid TRIVIAL, EASY drift, or unsolvable (0%-forever tests).

---

## Reviewer feedback (paste below)

```
[paste reviewer comments here]
```

---

## Step 1 — Inspect before editing (mandatory)

List the actual task tree. Read only real files.

For **each** reviewer point:

1. Quote the comment  
2. Map to exact file(s)  
3. Verdict: **Valid** | **Invalid** | **Partial** | **Defer**  
4. Planned change: **one sentence**, minimal scope  

**Do not start editing until this table is done.**

---

## Step 2 — Fix only what review requires

- Fix **only** valid reviewer issues and direct blockers  
- **Do not** refactor, add features, add/remove tests for difficulty tuning, rewrite instruction beyond review scope  
- **Do not** change `task.toml` difficulty/timeouts unless review requires it  
- **Do not** touch oracle/solution unless review or a test fix requires it  
- **Do not** create `rubric.md` unless user asks  

**Preserve:** agent pass band, anti-cheat, pinned Dockerfile deps, `allow_internet = false`, instruction ↔ test alignment.

---

## Step 3 — After edits

1. Docker build (if Dockerfile changed)  
2. Oracle → reward **1**  
3. NOP → reward **0**  
4. No new instruction-test gaps; no tests/solution in `environment/`  

---

## Step 4 — Output

| Reviewer point | Valid? | File(s) | Change made |
|----------------|--------|---------|-------------|

- **Intentionally not changed** (and why)  
- Commands + results  
- **Risk to difficulty/solvability:** none expected / explain  
- **Verified by execution:** yes/no  

Do not claim platform acceptance until re-upload and review pass.
