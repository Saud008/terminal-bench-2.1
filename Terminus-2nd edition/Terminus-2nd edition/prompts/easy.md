# Terminus — EASY label hardening (LOCKED — skip decorative Case 4/5)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Guards: `.cursor/rules/revise/hardness.mdc` (G-028–G-035) · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.

Use when the platform label is **`EASY`** (not merely “feels easy”), or when:

- **Worst** benchmark model pass rate is **>40%** (pre-emptive — new models inflate scores), **or**
- **GPT-5.5 (`terminus-gpt5-5`) ≥ 3/5** OR **Claude Opus 4.8 (`terminus-claude-opus-4-8`) ≥ 3/5**, **or**
- Per-test table shows **all tests ≥6/10** with no independent 0%-forever trap, **or**
- User says tasks keep landing EASY/TRIVIAL — **default Case 6** even without fresh platform stats.

**EASY ≠ “almost accepted.”** EASY means **do not upload again** until structural depth passes **`revise/trivial-hardening-probes.mdc`** (probes **1, 1b, 7, 8** minimum — all applicable PASS).

**New models (LOCKED):** **`terminus-gpt5-5`** and **`terminus-claude-opus-4-8`** pass tasks that were HARD under Opus 4.6 / GPT-5.2. **Case 6 is the default** for EASY — Case 5 is **deprecated** unless probes 1–9 PASS **and** user explicitly says “no structural change.”

**Not this router:** reviewer line comments only → **`prompts/reviewer.md`**. Oracle fail → **`oracleFix.md`**.

**Load with:** `revise/hardness.mdc`, `revise/trivial-hardening-probes.mdc`, `prompts/trivial-case-6.md`, `prompts/sp-hard-create-revise.md`, `shared/anti-trivial.mdc`, `@REVISE RULES`.

---

## One invoke

```text
@prompts/easy.md
Harden tasks/<task-name> — platform EASY.

Platform summary:
<paste Difficulty, Status, Agent Performance, Unit Tests Results>
```

**Agent must:** (1) quote EASY evidence, (2) run **Probe 1–7** table, (3) pick **Case 6 first** unless probes already PASS with structural depth, (4) implement **one** structural redesign, (5) oracle **1.0** + NOP **0.0**, (6) paste probe table before zip.

---

## EASY vs TRIVIAL (LOCKED)

| Label | Typical signal | First action |
|-------|----------------|--------------|
| **TRIVIAL** | Both models **5/5** or worst **>80%** | **Case 6** — skip Case 4/5 |
| **EASY** | Worst **>40%** or either model **≥3/5** | **Case 6** — Case 5 **forbidden** (G-031) |
| **Medium band** | Worst **≤40%** and both models **≤2/5** | Stop hardening — acceptable band |

**Do not** run `trivial-case-4.md`, `trivial-case-5.md`, or `trivial-harden.md` on EASY — structural Case 6 only.

---

## Mandatory diagnosis (before any edit)

Answer **yes/no** with file evidence:

| # | Question | If **yes** → |
|---|----------|----------------|
| 1 | One `BuildLedger` / `Normalize` / single export function does ingest + math + persist? | **Case 6** — split ingest → staging → export |
| 2 | Fixing `merge/apply.go`, `wrap.go`, or obvious “main bug file” passes bundled tests? | **Poison pill** — export must use **different module** (`export_stage.go`, `staging/publish.go`) |
| 3 | Hidden tests fail for **same** reason as bundled? | New **independent** hidden failure mode |
| 4 | Second EASY/TRIVIAL on **same slug**? | **Case 6 only** — no Case 5 (G-031) |
| 5 | Last revision added fields/tests only? | Revert decorative churn → structural fix |

---

## Auto-route (EASY — priority order)

| # | Condition | Action | File |
|---|-----------|--------|------|
| 1 | **Any** of diagnosis rows 1–2 **yes** | **Case 6** structural redesign | `trivial-case-6.md` |
| 2 | GPT **≥3/5** OR Claude **≥3/5** OR per-test **≥6/10** on all tests | **Case 6** (skip Case 4/5) | `trivial-case-6.md` |
| 3 | Probes 1, 1b, 7, or 8 **FAIL** | **Case 6** | `trivial-case-6.md` |
| 4 | **Default EASY** (no acceptable agent stats) | **Case 6** | `trivial-case-6.md` |
| 5 | Audit only | Read-only | `trivial-case-audit.md` |

**Deprecated on EASY:** rows for Case 5 / `trivial-harden.md` — use only if user explicitly overrides after Case 6 already shipped **and** probes 1–9 PASS.

---

## Required structural patterns (pick ONE — implement fully)

### A — Ingest snapshot + export stage (preferred Go/Rust CLI)

- Write `/app/state/<task>-snapshot.json` (or SQLite staging) on every recompute.
- **Export** reads snapshot only — **must not** re-parse input.
- **Broken export** uses `publishTracker` / `staging.ApplyLayer` — **not** the decoy `wrap.go` / `merge/apply.go`.
- Tests: `test_*_snapshot_matches_reference` + existing behavioral tests.
- Docs: `/app/docs/*-snapshot.md` cited in `instruction.md`.

### B — Second subcommand (`ingest` + `export`)

- `tool ingest` writes ledger/staging; `tool export` reads it.
- Export-only fix passes bundled; replay / second export fails without ingest fix.

### C — Poison-pill interaction (single CLI)

- Fix layer A breaks hidden until layer B fixed (mode switch, ratio open/closed, path-order vs type-batch).
- **Probe 4** must document the plausible wrong fix.

**Forbidden as “hardening”:** more hash fields, more pytest on same path, `difficulty = "hard"` only, instruction checklist.

---

## Pre-zip gates (LOCKED — G-028–G-035)

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

Paste **Probe 1–9** table from `revise/trivial-hardening-probes.mdc`. **Any FAIL → do not zip.**

| Gate | Block upload when |
|------|-------------------|
| **G-028** | Any probe FAIL |
| **G-029** | Go/Rust export CLI has no staging artifact + test for it |
| **G-030** | Export calls same broken helper agents are told to fix (no decoy split) |
| **G-031** | EASY/TRIVIAL revision without Case 6 structural change |
| **G-032** | One-file patch leaves **<60%** tests failing |
| **G-033** | Ingest-only fix passes export/replay hidden |
| **G-034** | Fewer than 2 independent hidden traps |
| **G-035** | First-upload Go/Rust/Bash CLI missing staging + decoy + chained poison |

---

## Target after resubmit

| Metric | Goal |
|--------|------|
| `terminus-claude-opus-4-8` | **≤20%** full reward (0% OK if fair) |
| `terminus-gpt5-5` | **≤40%** (ideally ≤20%) |
| Oracle / NOP | **1.0 / 0.0** |
| Verifier | No `verifier_did_not_run` |

Claude **timeout @ 1800s** with fair docs = valid hardness — **do not** weaken clock or hints to lift Claude.

---

## Related

- `prompts/trivial.md` — TRIVIAL label (both 5/5)
- `prompts/trivial-case-6.md` — full structural procedures
- `prompts/sp-hard-create-revise.md` — CREATE-time hardness
- `.cursor/rules/revise/hardness.mdc` — G-028–G-035 registry
