# MEDIUM Case 3 — Full unsolvable audit (MEDIUM label)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** **`difficulty = medium`** and **status not solvable**, but Case 1 routing is unclear — mixed signals, harness/oracle/zip issues, or multiple failure modes.

If **≥1 test is clearly 0%-forever** with fair docs → use **`medium-case-1.md`** instead.

If **`verifier_did_not_run`** or **oracle 0%** → `revise/oracle-fix-g025-g027.mdc` + `shared/runtime-verifier.mdc` first.

---

## Step 1 — Full inspect

Same as `hard-case-3.md`: task tree, instruction, docs, tests, Dockerfile, `test.sh`, oracle, zip (G-026, G-027).

Build:

| Issue class | Evidence | Fix path |
|-------------|----------|----------|
| 0%-forever test | per-test table | Case 1 alignment |
| Harness / verifier | no reward.txt, tmux | runtime-verifier |
| Oracle offline | G-025 | oracle-fix |
| Doc contradiction | agent + platform analysis | docs + instruction |

---

## Step 2 — Minimal fair fix

Fix **root cause only**. Do not harden until solvable.

---

## Step 3 — Verify + output

Oracle **1**, NOP **0**. Report solvable yes/no, target **MEDIUM** until re-eval.

For full step detail, also read `prompts/hard-case-3.md` (same diagnosis pattern; adjust difficulty target to MEDIUM).
