# Reviewer feedback — RF4 (full locked triage workflow — default)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Standard **NEEDS_REVISION** with reviewer line comments. This is the **default** reviewer prompt.

Same policy as `.cursor/rules/reviewer/REVIEWER-RULES.mdc` — triage before edit.

---

## Context

- Task was **rejected** on review; agent eval may or may not be acceptable.
- **Goal:** pass review with **minimal required changes** — avoid TRIVIAL, EASY drift, or unsolvable traps.

---

## Reviewer feedback (paste below)

```
[paste reviewer comments here]
```

---

## Step 1 — Inspect before editing (mandatory)

List the actual task tree under this task. Read only real files: `instruction.md`, `task.toml`, `environment/Dockerfile`, `tests/test.sh`, `tests/test_outputs.py`, `solution/`, `environment/docs/`.

For **each** reviewer point:

| # | Comment (quote) | File(s) | Verdict | Planned change (one sentence) |
|---|-----------------|---------|---------|-------------------------------|

Verdict: **Valid** (must fix) | **Invalid** (reject with guideline cite) | **Partial** | **Defer**

**Do not start editing until this table is done.**

---

## Step 2 — Fix only what review requires

- Fix **only** valid reviewer issues and direct blockers  
- **Do not** refactor, rename broadly, add features  
- **Do not** add/remove tests for difficulty unless review explicitly asks  
- **Do not** rewrite instruction beyond review (≤3 short paragraphs, absolute paths)  
- **Do not** change difficulty/timeouts/metadata unless review requires  
- **Do not** touch oracle unless review or test fix requires it  
- **Do not** create `rubric.md` in repo unless user asks  

**Preserve:** anti-cheat, no runtime installs in `test.sh`, verifier in Dockerfile, `allow_internet = false`, `workdir = "/app"`.

If feedback would trivialize: **smallest compliant alternative** + note tradeoff.

---

## Step 3 — After edits, regression check (mandatory)

1. Docker build (if image changed)  
2. `harbor run -a oracle -p tasks/<name> --debug` → reward **1**  
3. `harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-...` → reward **0**  
4. Re-check instruction-test alignment  
5. Optional: ruff on task Python; `run_static_checks.py`  

**Do not** claim ready without oracle + NOP evidence.

---

## Step 4 — Output

| Reviewer point | Valid? | File(s) | Change made |
|----------------|--------|---------|-------------|

- **Intentionally not changed** (and why)  
- Commands run + results  
- **Risk to difficulty/solvability:** none expected / explain  
- **Verified by execution:** yes/no  
