# Terminus — Reviewer feedback prompts (auto-router)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


Use when the platform or human reviewer returns **line comments** or **NEEDS_REVISION** text.

**Not this router:** bare platform labels (**TRIVIAL**, **EASY**, **oracle fail**, **unsolvable**, **verifier did not run**) → **`prompts/easy.md`** / **`prompts/trivial.md`** / Phase D — **not** this file unless line comments present.

**Load with:** `.cursor/rules/reviewer/REVIEWER-RULES.mdc` (LOCKED), `shared/task-lifecycle.mdc` Phase D′, `shared/task-lifecycle.mdc` §3, `shared/anti-trivial.mdc`, **`revise/hardness.mdc` (G-028–G-035)** when feedback mentions difficulty / trivial / easy agents.

**Difficulty escalation (LOCKED — Jun 2026 models):** Benchmark agents = **`terminus-claude-opus-4-8`**, **`terminus-gpt5-5`**. If reviewer or platform says agents pass too easily, task is **EASY/TRIVIAL**, per-test **≥6/10 on all tests**, or **either** agent **≥3/5** — **do not** use RF3 “preserve difficulty.” Route to **`prompts/easy.md`** or **`prompts/trivial-case-6.md`** after RF6 triage. RF3 applies **only** when **both** agents **≤2/5**, worst **≤20%**, **and** feedback is CI/metadata only.

**Paths:** edit in place — `tasks/<name>/` → `tasksubmit/<name>.zip`.

---

## One invoke — agent auto-picks RF

Paste reviewer feedback only. **Do not ask the user to pick RF1–RF6.** Parse feedback, route, then load the chosen `reviewer-feedback-*.md` **in full**.

```text
@prompts/reviewer.md
Fix tasks/<task-name> per reviewer feedback below.
Do not trivialize. Re-run oracle + NOP after behavior/test changes.

Reviewer feedback:
<paste line comments or NEEDS_REVISION text>
```

**Agent must:** (0) read **`jobs-local/reviewer-feedback-gate-last.json`** if hook ran, (1) parse feedback → pick RF using table below, (2) **state chosen RF + why** before edits, (3) triage each comment Accept/Reject/Partial/Defer **vs accepted-feedback A-001…A-010**, (4) fix only valid items with **minimal diff** — **reject** if fix would make task TRIVIAL/EASY, (5) oracle 1.0 + NOP 0.0 before resubmit.

**Automatic on paste:** `scripts/reviewer_feedback_gate.py` compares reviewer text to accepted corpus gates + trivial-risk. **Do not apply** REJECT rows. If verdict `ROUTE_CASE6` → **`trivial-fix-invoke.md`** + Case 6, not cosmetic reviewer compliance.

---

## Auto-route from reviewer feedback (mandatory)

### Step A — Parse feedback

For each comment, note:

| Signal | Examples |
|--------|----------|
| **Metadata / CI only** | `timeout_sec`, `build_timeout_sec`, reward block, `-rA`, ruff F401, `subcategories`, `codebase_size`, `.dockerignore`, `allow_internet`, `workdir` |
| **Banned category / classifier** | `category` not in allowlist (`security` / `cloud-devops` / `system-configuration-and-setup` / `build-and-dependency-management`), or `[category_classifier] Predicted category '…' is blocked` → fix `task.toml` + reframe instruction/tags **first** (`shared/task-toml-category-gate.mdc`) |
| **Verifier / harness** | `test.sh` installs, CTRF, `verifier_did_not_run`, Dockerfile pytest pins |
| **Alignment / fairness** | instruction-test gap, contract doc missing behavior, format-only tests, anti-cheat gap |
| **Trivializing risk** | patch `/app/src/...`, exact bug file, golden output in env, drop tests, BUG comment, exact operator in instruction, test checklist in instruction |
| **Agent eval context** | “agent runs good”, “agent eval acceptable”, “do not change difficulty”, “rejected on review only” |
| **Difficulty / trivial** | “too easy”, “TRIVIAL”, “EASY”, “5/5 agents”, “one-file fix”, “add hints” |
| **Verify loop** | “run oracle/NOP”, “quality 11/11”, “static checks”, “rerun until pass” |
| **Linux user/password** | unix user, `chpasswd`, non-root user in image |

### Step B — Pick RF (priority order — first match wins)

| # | Condition in pasted feedback | RF | File |
|---|------------------------------|-----|------|
| 0 | Platform label only (TRIVIAL / EASY / oracle / unsolvable / verifier) — **no** line comments | — | Use **`prompts/easy.md`** (EASY) or **`prompts/trivial.md`** (TRIVIAL) — **not** this file |
| 0b | Reviewer says **too easy / trivial / agents ≥3/5** with or without line comments | — | **`prompts/easy.md`** or **`trivial-case-6.md`** — **before** RF4 |
| 1 | **Any** trivializing signal (patch path, golden leak, drop tests, BUG hint, solution steps) **OR** user says “triage first” | **RF6 → then RF4 or easy.md** | [`reviewer-feedback-6.md`](reviewer-feedback-6.md) — if difficulty signal → **easy.md** not RF4 alone |
| 2 | **Only** timeout/password/metadata/CI blockers — **no** test, instruction, oracle, or behavior changes | **RF1** | [`reviewer-feedback-1.md`](reviewer-feedback-1.md) |
| 3 | Agent eval **acceptable** / “do not change difficulty” **and** **both** models **≤2/5** **and** worst **≤20%** (not EASY/TRIVIAL) | **RF3** | [`reviewer-feedback-3.md`](reviewer-feedback-3.md) |
| 4 | Primary ask is **re-verify** (oracle/NOP/quality/static/11/11) after a small known fix | **RF2** | [`reviewer-feedback-2.md`](reviewer-feedback-2.md) |
| 5 | Broad checklist + explicit **difficulty recheck** / rubric / behavior-test audit | **RF5** | [`reviewer-feedback-5.md`](reviewer-feedback-5.md) |
| 6 | **Default** — mixed line comments, alignment, tests, instruction, Dockerfile | **RF4** | [`reviewer-feedback-4.md`](reviewer-feedback-4.md) |

### Step C — Anti-trivial guard (all RF)

Before and after edits, confirm:

- Do **not** add bug locations, fix steps, or golden answers to `instruction.md` or `environment/`
- Do **not** drop or weaken tests unless comment is **invalid** — push back via RF6
- Do **not** change `difficulty` or agent-facing scope unless review **requires** it
- Preserve **≥6 interacting bugs** on revision (target **6+** for new tasks); **≥5 modules** with ingest + export + decoy when Go/Rust CLI (`revise/hardness.mdc` G-029–G-033)
- After **any** test or behavior edit: paste **`revise/trivial-hardening-probes.mdc`** table — probes **1, 1b, 7, 8** minimum; **G-028** blocks zip if any FAIL
- If reviewer comment would **reduce** difficulty (drop hidden tests, add hints) while agents **≥3/5** → **Reject** and route **`easy.md`** / Case 6

If applying feedback exactly would trivialize → **Reject** or **Partial** with smallest compliant alternative.

**Reject (do not apply) reviewer feedback that:**

- Names bug files, operators, or fix order in `instruction.md`
- Adds golden outputs to `environment/`
- Drops hidden tests because “agents struggle”
- Suggests lowering difficulty or adding step-by-step solve hints for EASY/TRIVIAL

### Step D — Execute

1. Load chosen `reviewer-feedback-N.md` **in full**
2. Inspect real task files — no guessing
3. Triage table **before** edits (RF4/RF6 require it; RF1 may skip if scope is metadata-only)
4. Minimal fix only
5. `harbor run -a oracle` → **1.0**; `harbor run -a nop` → **0.0** when behavior/tests change
6. Repack `tasksubmit/<name>.zip` if user path is `tasks/`

---

## Quick routing (decision tree)

```
IF platform TRIVIAL label only → prompts/trivial.md (NOT this file)
IF platform EASY label only → prompts/easy.md (NOT this file)
IF reviewer/platform says too easy / 5/5 agents → easy.md or trivial-case-6.md (after RF6 triage)

IF any trivializing hint OR "triage first"
  → RF6 (triage + pushback) → then RF4 for fixes

ELSE IF only timeout / password / static metadata (no behavior change)
  → RF1

ELSE IF agent eval OK + preserve difficulty
  → RF3

ELSE IF main ask = oracle/NOP/quality/static rerun
  → RF2

ELSE IF broad checklist + difficulty recheck
  → RF5

ELSE
  → RF4 (default)
```

**Never:** commit API keys, tokens, or passwords into the repo.

---

## RF reference

| RF | File | When auto-selected |
|----|------|-------------------|
| RF1 | `reviewer-feedback-1.md` | Metadata/timeouts/password only |
| RF2 | `reviewer-feedback-2.md` | Verify loop is primary ask |
| RF3 | `reviewer-feedback-3.md` | Agent eval OK; minimal review fix |
| RF4 | `reviewer-feedback-4.md` | **Default** — mixed reviewer comments |
| RF5 | `reviewer-feedback-5.md` | Checklist + difficulty recheck |
| RF6 | `reviewer-feedback-6.md` | Trivializing risk — triage before edit |

---

## Explicit override (optional)

```text
@prompts/reviewer.md — RF4
Fix tasks/<task-name> per prompts/reviewer-feedback-4.md
```

Use only when you want to force a case; otherwise paste feedback and let the router decide.
