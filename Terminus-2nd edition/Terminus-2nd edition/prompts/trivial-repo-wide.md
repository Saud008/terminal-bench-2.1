# TRIVIAL — Repository-wide reasoning contract (LOCKED)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**Purpose:** Tasks hardened from **TRIVIAL/EASY** must require **repository-wide reasoning**. A correct agent solution cannot be an isolated patch in one file.

**SP (Jun 2026):** Primary hardness benchmark = **`terminus-claude-opus-4-8`** (`platform-preferences.mdc` §1b). GPT-5.5 may remain high — deepen **scope** (multi-module + state + docs) under **`[agent] timeout_sec = 1800`**, not agent clock tricks. Wrapper: `sp-hard-create-revise.md`.

**Load with:** every TRIVIAL edit case (`trivial-case-1`, `trivial-case-2`, `trivial-case-6`, `trivial-tb3-hardening`) and when authoring new tasks that must resist shallow fixes.

**Paths:** edit in place — `tasks/<name>/` → `./scripts/pack_zip.sh <name>` → `tasksubmit/<name>.zip`.

---

## Before making changes (mandatory)

Identify **all subsystems** that participate in the affected workflow, including:

- validation
- business logic
- persistence
- serialization / deserialization
- caching
- state management
- reporting
- command execution
- APIs and CLIs
- supporting utilities

Map them on paper (or in your triage output) before editing. A one-file fix that leaves another subsystem wrong is **incomplete**.

---

## 1. Architectural consistency

- Follow existing repository conventions and design patterns.
- Reuse existing abstractions wherever possible.
- Do **not** introduce parallel implementations of existing functionality.
- Avoid special-case logic that bypasses established architecture.
- Resolve ambiguity by examining related implementations already present in the codebase.

---

## 2. Backward compatibility

- Preserve compatibility with existing data.
- Preserve existing serialization formats.
- Preserve existing configuration formats.
- Preserve existing public interfaces.
- Preserve existing CLI and API behavior unless explicitly required otherwise.
- Existing user workflows should continue to function without modification.

---

## 3. State consistency

- Maintain a **single source of truth** for all affected state.
- Prevent divergence between canonical state and derived state.
- Ensure all readers and writers observe consistent behavior.
- Any state modification must be reflected across all dependent subsystems.
- State reconciliation must remain correct after recovery operations.

---

## 4. Multi-stage workflow correctness

The implementation must remain correct across:

- initial execution
- repeated execution
- interrupted execution
- partial completion
- recovery scenarios
- rollback scenarios
- restart scenarios
- replay scenarios
- idempotent operations
- out-of-order operations where supported

Behavior must remain **deterministic** regardless of execution sequence.

---

## 5. Cross-module invariants

The repository contains invariants that may not be explicitly documented.

These invariants must continue to hold across:

- validation
- storage
- business logic
- serialization / deserialization
- reporting
- interfaces
- user-visible outputs

Changes that satisfy only one subsystem while violating another are **incorrect**.

---

## 6. Edge case handling

The implementation must correctly handle:

- empty inputs
- boundary conditions
- duplicate operations
- repeated processing
- partial state
- stale state
- invalid transitions
- conflicting updates
- recovery from incomplete execution

The solution should remain robust under all supported execution paths.

---

## 7. Ordering-sensitive behavior

Correctness must **not** depend on a single happy-path execution order.

The implementation must account for:

- operation sequencing
- state transitions
- replay behavior
- dependency ordering
- repeated application of actions

Equivalent workflows should converge to equivalent results.

---

## 8. Persistence guarantees

Any persisted state must:

- survive restart cycles
- reload correctly
- remain internally consistent
- remain compatible with historical data
- remain compatible with future processing

Persistence-related behavior should remain deterministic.

---

## 9. Refactoring requirements

If duplicated logic contributes to the problem:

- consolidate behavior into reusable abstractions
- avoid copy-paste implementations
- avoid introducing additional duplication

The final implementation should **reduce** maintenance burden rather than increase it.

---

## 10. Test resistance (anti-shallow)

Solutions will be evaluated beyond visible failures.

**Incorrect** agent or oracle shortcuts include:

- hardcoded outputs
- test-specific logic
- narrow fixes targeting a single execution path
- implementations that pass only current tests
- implementations that ignore dependent subsystems
- implementations that rely on undefined behavior

**Hardening must add tests** that fail until **multiple** subsystems are repaired — not until one grep or one JSON file is patched.

---

## 11. Performance and stability

The solution must:

- avoid unnecessary complexity
- avoid performance regressions
- preserve existing scalability characteristics
- preserve deterministic behavior
- avoid introducing global mutable state unless already required by architecture

---

## 12. Expected approach

Solve by understanding the repository's architecture, invariants, and workflow interactions.

Implementations that merely patch the immediately visible failure — without addressing related execution paths, persistence behavior, ordering semantics, state consistency, and subsystem interactions — are **incomplete**.

A successful solution demonstrates complete understanding of how the affected functionality interacts with the broader system.

---

## Terminus hardening checklist (apply after §1–§12)

When **authoring or revising** a task under TRIVIAL hardening:

| Check | Required |
|-------|----------|
| **4+ bugs** across **3+ modules** | yes — isolated patch insufficient |
| **Cross-run** tests (replay, resume, idempotency, stale cache) | where domain fits |
| **Independent reference** in `tests/` | anti-cheat; no golden in `environment/` |
| **Contracts** in `/app/docs/` | no test-only hidden rules |
| **Oracle** fixes real code paths | not artifact-only |
| **NOP** fails until broad repair | reward **0** |
| **Solvable** | oracle **1**; design not **0/5 forever** |
| **Verifier stable** | `runtime-verifier.mdc`; no `verifier_did_not_run` |

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

---

## Output (when used as hardening prompt)

Report:

1. **Subsystem map** — modules touched by the workflow  
2. **Invariant list** — what must hold across validation → persistence → export  
3. **Bug interaction map** — why one-file fix is insufficient  
4. **New traps / tests** — which subsystems each test exercises  
5. **Solvability guard** — oracle/NOP evidence; confirm not 0/5-forever design
6. **Probe table** — from `revise/trivial-hardening-probes.mdc` (PASS/FAIL before zip)

---

## 13. Decorative hardening anti-patterns (LOCKED — Jun 2026)

Case 5 **failed** on platform when authors only:

- Added `audit_hash`, `input_fingerprint`, `dedupe_key` tweaks, or extra JSON fields
- Wrote the new rule clearly in `/app/docs/` so agents implement in one read
- Left **core bugs sequential** (fix math → fix export → 100% pass)
- Added hidden tests that fail for the **same** bug as bundled tests

**Decorative hardening does not count.** Before zip, run probes in **`revise/trivial-hardening-probes.mdc`**.

**Required interaction depth:**

- **Poison pill:** partial fix passes some bundled tests but **hidden** reference fails
- **Two layers:** persistence wrong while math looks right (or reverse)
- **Order vs sort:** merge/precedence uses **file order**, epoch, or journal — not alphabetical convenience
- **Cross-run:** second CLI invocation or replay exposes bug invisible on first run

If **5/5 persists after Case 5** → **`prompts/trivial-case-6.md`** (structural redesign), not more fields.

---

## 14. Mandatory pre-zip probes (LOCKED)

| Probe | Pass when |
|-------|-----------|
| **1 Single-file patch** | ≥40% tests still fail (≥50% if platform was 5/5) |
| **2 Omit persistence fix** | sequence/replay/idempotency tests fail |
| **3 Hidden ≠ bundled root** | hidden fails under partial fix that passes bundled |
| **4 Almost-correct trap** | plausible wrong layer passes some checks, fails hidden |
| **5 Doc depth** | ≥3 cited docs needed for hidden; no one-paragraph recipe |
| **6 Second+ TRIVIAL** | structural redesign per Case 6, not test inflation |

Full procedure: **`revise/trivial-hardening-probes.mdc`**.

