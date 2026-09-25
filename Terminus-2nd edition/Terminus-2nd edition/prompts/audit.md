# Terminus — Post-creation audit (Phase C)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When:** Immediately **after creating** a new task (A→H pipeline Phase E / lifecycle Phase C), **before** verify/zip.

**CREATE AUTO MODE (LOCKED):** After Phase D, agents **start audit in the same turn without asking the user**. Do **not** end with “task created — want audit?”. Follow **`create/post-create-audit-loop.mdc`** + **`shared/sanjana-standing-requirements.mdc`** — fix **High → Medium → optional Low**; 2–4 rounds; stop early when clean. Run `scripts/post_create_audit_loop.py` each round.

**Read-only** for user-invoked standalone audit **unless** the user asks to fix.

---

## Mandatory load order (agent must follow)

Use **all three** together — not `audit.md` alone:

| Order | Tag / file | Role |
|-------|------------|------|
| 1 | **`@prompts/audit.md`** (this file) | Audit steps + report format |
| 2 | **`@AUDIT RULES`** — `audit/AUDIT-RULES.mdc` | Structural checklist + difficulty gate |
| 3 | **`@REVIEWER RULES`** — `reviewer/REVIEWER-RULES.mdc` | Reviewer severity + fairness/triviality lens |
| 4 | **`reviewer/reviewer-checklist.mdc`** | **Full Snorkel TB2 checklist** — every applicable criterion |

Also load: `shared/spec.mdc`, `shared/runtime-verifier.mdc`, `shared/dockerfile.mdc`, `shared/anti-trivial.mdc`, `shared/accepted-corpus.mdc`, `shared/platform-preferences.mdc` §1b (benchmark agents **`terminus-claude-opus-4-8`**, **`terminus-gpt5-5`**).

**Do not flag:** missing local `rubric.md`, `author_name`, or `author_email` (repo policy — rubric in UI is OK).

---

## Invoke (copy-paste after every new task)

```text
@prompts/audit.md
@AUDIT RULES
@REVIEWER RULES

Audit tasks/<task-name> against Terminus rules.

First inspect the real task directory and list actual files found. Do not assume any file exists.
Apply reviewer/reviewer-checklist.mdc in full using @REVIEWER RULES severity guidance.
Do not modify files yet.
```

**Agent must:**

1. Load all four sources above before auditing  
2. List real files (inventory)  
3. Run Steps 2–11 below **and** map each failed `reviewer-checklist.mdc` item into the report  
4. Classify every issue with reviewer severity (High / Medium / Low)  
5. **Do not edit** unless user asks to fix  

---

## Step 1 — Inventory (mandatory)

1. List **actual** task tree (every path that exists).
2. Classify: **milestone** vs **non-milestone**.
3. Verify root structure matches task type (see `zip/upload-zip.mdc`).

---

## Step 2 — Structural and metadata checks

| Check | What to verify |
|-------|----------------|
| `task.toml` required fields | `[agent] timeout_sec`, `[verifier] timeout_sec`, `[environment]` block |
| `allow_internet` | `false` |
| `workdir` | `"/app"` for non-milestone (unless platform schema explicitly rejects) |
| Metadata | `category`, **`subcategories = []`**, `language`, `difficulty` (`medium`/`hard` only), `codebase_size` (`small`/`large`/`minimal` — not `medium`) |
| Tags | ≤6 |
| Milestone | `steps/milestone_N/` only if milestone; no root `instruction.md` / `tests/` / `solution/` |

---

## Step 3 — Dockerfile and environment

- Base image **digest-pinned** or CI-compatible pinning (`shared/dockerfile.mdc`)
- **tmux** and **asciinema** installed
- All app + verifier dependencies **pinned** and **preinstalled** (e.g. `/opt/verifier-venv`, pytest pins)
- Toolchains on PATH if needed (`cargo`, `go`, `mvn`, symlinks)
- **No** `tests/`, `solution/`, expected outputs, ground truth, hidden hints in agent image
- No BUG / verifier / pytest / grading wording in agent-visible files
- No AI scaffolding filenames (`CLAUDE.md`, `skills.md`, etc.)
- `environment/.dockerignore` covers caches, `target/`, `__pycache__`, `.git`
- `codebase_size` backed by **meaningful** files — not filler

---

## Step 4 — Verifier (`tests/test.sh`)

- **No** runtime installs/downloads (`pip`, `apt`, `curl`, `npm`, `uv`, playwright install, etc.)
- `mkdir -p /logs/verifier` at start
- Prewrite `reward.txt` to `0`; minimal `ctrf.json` before early exits where possible
- Explicit `cd /app` — do not rely on Docker `WORKDIR` alone
- Ends with platform reward block: `if [ $? -eq 0 ]` — **nothing after closing `fi`**
- Same verifier logic for oracle and agent

---

## Step 5 — Instruction

- ≤3 short paragraphs; natural user tone
- **Absolute paths** only
- No task name / canary strings
- No solution hints, step-by-step fixes, or pytest-checklist wording
- Contracts/schemas in `/app/docs/` — referenced, not duplicated as spoilers
- **Instruction ↔ test alignment** — every tested behavior documented; no hidden test-only rules

---

## Step 6 — Tests

- Docstrings on test functions
- **Behavior-based** — CLI/API/file bytes + independent reference recompute
- Not **only** format/source-string grep (unless contract requires source)
- Force **real code execution** and **rebuild-from-source** where applicable
- Anti-cheat: checksums, hidden fixtures under `tests/` only, mutated payloads, idempotency/replay where fit
- Hidden requirements absent

---

## Step 7 — Oracle (`solution/solve.sh`)

- **Deterministic**; no network (G-025 offline)
- Fixes **real implementation** — not hardcoded final artifacts
- Not a tutorial that agents could copy
- Idempotent where possible

---

## Step 8 — Rubric (UI / platform — do not require local `rubric.md`)

- Behavior-based criteria only
- Valid score balance for live rubric checker
- **≥3 distinct negative criteria** (can be done in UI)
- No references to docs/tests/verifier/pytest/instruction/oracle/NOP in rubric lines

---

## Step 9 — @REVIEWER RULES + full checklist (mandatory)

**Read `reviewer/reviewer-checklist.mdc` end-to-end.** For each section that applies to this task, record **Pass / Fail / N/A**.

Apply **`@REVIEWER RULES`** lens while auditing (read-only — no reviewer feedback to triage yet):

- Would a proposed “fix” in the audit report **trivialize** the task or **leak** the solution? If yes → note safer alternative in `fix` field.
- Use checklist **severity guidance**: any **High** fail → not ready; multiple **Medium** fails → not ready.

**Checklist sections to cover (minimum):**

| Section | reviewer-checklist.mdc topics |
|---------|------------------------------|
| Instruction | concise, well-specified, interesting, no hints, no env leakage |
| Environment | realistic docs, no hidden walkthroughs, pinned deps, no solution in image, no AI scaffolding |
| Tests | aligned, behavioral, anti-cheat, no runtime installs |
| Oracle | same path as agents, real fixes |
| Metadata | `subcategories = []`, difficulty evidenced |
| Rubric (UI) | behavior-based, ≥3 negatives, valid scores — skip local file if absent |

Output a **Reviewer checklist table** in the final report:

| Checklist item (short) | Pass/Fail/N/A | Severity if Fail | Evidence (file:line or observation) |
|------------------------|---------------|------------------|-------------------------------------|

---

## Step 10 — Difficulty and non-triviality gate

| Question | Required analysis |
|----------|-------------------|
| Bugs/behaviors | List **3–5 distinct** bugs or repairs with source locations |
| Interaction | Do bugs interact or are they independent one-liners? |
| Shallow patch | Why can a **one-file shallow patch NOT** pass? If it can → **too easy** |
| Real execution | Which tests force CLI/API/library execution? |
| Rebuild | Which tests verify behavior after **rebuild from source**? |
| Hardcoding | Why can **hardcoded output NOT** pass? |
| Failure modes | ≥3 realistic mistakes weaker agents will make |
| Difficulty evidence | **Target only** vs **verified** (oracle/NOP/agent runs) |

If too easy: propose harder changes **without hidden requirements** (do not edit unless asked).

---

## Step 11 — Verification status (report only)

State whether these were **run in this session** with evidence:

- Docker build
- `harbor run -a oracle` → reward 1
- `harbor run -a nop` → reward 0
- Static checks / ruff if applicable

If not run → **not verified by execution**.

---

## Report format (every issue)

```
severity: High | Medium | Low
file/path: <exact path>
problem: <exact problem>
fix: <exact fix needed>
```

**Final summary (required):**

| Field | Value |
|-------|-------|
| Task type | milestone / non-milestone |
| Ready to submit | Yes / No |
| Verified by execution | Yes / No |
| Difficulty | target only / verified |
| Triviality risk | Low / Medium / High |
| Blockers (High) | list |
| Reviewer checklist failures | list by section (from Step 9 table) |

**Do not say ready** unless every **High** checklist item and audit item passes with evidence.

**After audit:** fix blockers → `@VERIFY RULES` → `@ZIP RULES`.
