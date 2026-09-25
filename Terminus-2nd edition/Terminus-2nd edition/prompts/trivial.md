# Terminus — TRIVIAL / EASY hardening prompts (auto-router)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


Use when the platform labels the task **TRIVIAL** or **EASY**, or agent eval shows **`terminus-claude-opus-4-8`** or **`terminus-gpt5-5`** passing too easily (either **≥3/5** or worst **>60%**).

**Benchmark agents (LOCKED):** **`terminus-claude-opus-4-8`**, **`terminus-gpt5-5`**. New models pass more than Opus 4.6 / GPT-5.2 — treat **≥3/5 on either** as Case 6 signal (`revise/hardness.mdc` G-031).

**Case choice = summary only.** Match **first row** in Step B below — do **not** pick Case 4, Case 6, or any case without summary evidence. The @ tag does not select the case.

**Not this router:**

- **Unsolvable / 0%-forever tests** with difficulty already HARD → **`prompts/hard.md`**
- **Reviewer line comments** only → **`prompts/reviewer.md`**
- **Oracle fail / verifier did not run** only → `revise/oracle-fix-g025-g027.mdc` + `shared/runtime-verifier.mdc`

**Load with:** `shared/task-lifecycle.mdc` Phase D, `shared/anti-trivial.mdc`, `shared/first-pass-blueprint.mdc` §3, `shared/runtime-verifier.mdc`, `shared/dockerfile.mdc`.

**Paths:** edit in place — `tasks/<name>/` → `./scripts/pack_zip.sh <name>` → `tasksubmit/<name>.zip`.

---

## One invoke — agent auto-picks case

Paste **task name**, **platform summary**, and **agent artifacts** (per-test pass table if available). **Do not ask the user to pick a case.**

```text
@prompts/trivial.md
Harden tasks/<task-name> — currently TRIVIAL/EASY on platform.

Platform summary:
<paste Difficulty, Status, Agent Performance, Unit Tests Results>

Artifacts:
<paste per-test pass rates, failure logs, reviewer notes if any>
```

**Agent must:** (1) inspect real task files + artifacts, (2) **state chosen case + why**, (3) classify each test as keep/replace/deepen, (4) harden for **real semantics** — **hard AND solvable**, (5) oracle **1.0** + NOP **0.0**, (6) no `verifier_did_not_run`.

---

## Target difficulty (LOCKED — do not overshoot)

| Metric | Target | Avoid |
|--------|--------|-------|
| Worst strong model | **~1/5 (≈20%) or lower** | **0/5 forever** (broken/unsolvable on auto-eval) |
| Best strong model | **occasionally passes** (1–2/5 OK) | **5/5** (still trivial) |
| Oracle | **100%** | oracle writes artifacts only |
| NOP | **0%** | NOP passes |
| Verifier | stable every run | flaky, timing, `verifier_did_not_run` |

**Do not use “target 1/5 only” as sole goal** — that risks unsolvable. Harden through **interacting behavior**, not missing specs or broken harnesses.

---

## Auto-route from platform evidence (mandatory)

### Step A — Parse summary

1. **Full-suite:** `terminus-claude-opus-4-8` X/5, `terminus-gpt5-5` Y/5 (reward 1 = pass).
2. **Per-test table:** mark tests **consistently solved** vs **partially solved / hard**.
3. **Reviewer history:** already flagged trivial? TB3 / language shallow?
4. **Verifier:** any `verifier_did_not_run` or oracle/NOP issues?

### Step B — Pick case (priority order — first matching row wins)

| # | Summary signal | Case | File |
|---|----------------|------|------|
| 0 | User says **audit only** / **read-only** / **do not modify** | Audit | [`trivial-case-audit.md`](trivial-case-audit.md) |
| 1 | **Unsolvable** / 0%-forever / not solvable (unfair) | — | **`prompts/hard.md`** instead |
| 2 | TB3 rebuild, shallow Python, verifier instability, language migration | TB3 | [`trivial-tb3-hardening.md`](trivial-tb3-hardening.md) |
| 3 | Label **EASY**, either model **≥3/5**, worst **>40%**, or all per-tests **≥6/10** | **Case 6** | [`trivial-case-6.md`](trivial-case-6.md) — load [`easy.md`](easy.md) when label is **EASY** |
| 4 | Label **TRIVIAL**, **both models 5/5**, second+ TRIVIAL on slug, one-file patch passes, probes FAIL, decorative hardening | **Case 6** | [`trivial-case-6.md`](trivial-case-6.md) + [`revise/trivial-hardening-probes.mdc`](../.cursor/rules/revise/trivial-hardening-probes.mdc) |
| 5 | Reviewer/platform **already flagged trivial** — do not resubmit same form | **Case 1** | [`trivial-case-1.md`](trivial-case-1.md) |
| 6 | Still trivial but **both models ≤2/5** — deepen without full redesign | **Case 2** | [`trivial-case-2.md`](trivial-case-2.md) |
| 7 | **Default** — any other TRIVIAL/EASY signal | **Case 6** | [`trivial-case-6.md`](trivial-case-6.md) |

**Agent must:** quote which row matched and **why** before editing. **`Read`** the chosen case file + [`trivial-repo-wide.md`](trivial-repo-wide.md) for edit cases.

### Step C — Shared hardening rules (all edit cases)

**Keep:**

- Tests agents **partially** solve or fail for **semantic** reasons
- Cross-file reasoning, state, ordering, replay, persistence, recovery
- Oracle/verifier path unless genuinely flawed

**Replace / strengthen:**

- Tests all agents solve easily
- One-function / one-file patch bugs
- Hardcoded-output shortcuts, shallow parser-only fixes
- Tests that skip real runtime behavior

**Increase difficulty through:**

- 4+ subtle bugs across 3+ modules that **interact**
- Delayed-effect, replay/idempotency, persistence across runs
- Ordering-sensitive output, stale-state recovery, corrupt partial state
- Hidden/dynamic fixtures under `tests/` only; independent reference recompute
- Multi-step workflows where one subsystem fix affects another
- **Ingest → staging artifact → export** pipeline with **decoy** fix file off export hot path (`revise/hardness.mdc` G-029, G-030)

**Do not:**

- Relabel `difficulty` only; grep-only tests; golden leaks in `environment/`
- BUG / verifier / pytest wording in agent-visible files
- Runtime installs in `test.sh`; `allow_internet` must stay **false**
- Make **unsolvable** (oracle fail, NOP pass, 0/5 forever)
- Create `rubric.md` in repo unless user asks (platform rubric is separate)

### Step D — Verifier stability (all edit cases)

Before claiming done, fix `tests/test.sh` if needed:

- `mkdir -p /logs/verifier` at start
- Prewrite `reward.txt` to `0`; minimal `ctrf.json` before early exits
- Explicit `cd /app`; never exit only because `$PWD` is `/`
- No runtime installs; deps in `environment/Dockerfile`
- Platform-compatible final reward block (`if [ $? -eq 0 ]`)

### Step E — Verify loop

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

Optional: static checks, `collapse_check.py`, Docker build.

**Do not claim “non-trivial” or “accepted” without oracle/NOP evidence.** Platform agent stats confirm difficulty after resubmit.

---

## Quick routing

```
IF audit only → trivial-case-audit.md
IF unsolvable / 0%-forever unfair → hard.md
IF platform EASY OR either model ≥3/5 OR worst >40% → easy.md → Case 6
IF TB3 / shallow stack / verifier unstable → trivial-tb3-hardening.md
IF TRIVIAL OR either model ≥3/5 OR per-test ≥6/10 → trivial-case-6.md (skip Case 4/5)
IF probes FAIL → trivial-case-6.md
IF both models ≤2/5 AND worst ≤20% → trivial-case-2.md
ELSE → trivial-case-6.md (NOT trivial-harden.md)
```

---

## Case reference

| Case | File | When |
|------|------|------|
| Audit | `trivial-case-audit.md` | Review + plan only — **no edits** |
| TB3 | `trivial-tb3-hardening.md` | Full reconstruction + verifier stability |
| 1 | `trivial-case-1.md` | Repeat trivial flag — major rework |
| 2 | `trivial-case-2.md` | Deeper behavior, not shallow edge cases |
| 6 | `trivial-case-6.md` | **Default** TRIVIAL/EASY — ingest→staging→export + decoy (G-031) |
| Probes | `revise/trivial-hardening-probes.mdc` | **Before zip** — probes 1–9 |
| Repo-wide | `trivial-repo-wide.md` | **Load with every edit case** — §1–§14 contract |
