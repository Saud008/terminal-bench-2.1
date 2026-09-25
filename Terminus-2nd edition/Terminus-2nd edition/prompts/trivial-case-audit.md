# TRIVIAL / EASY — Audit only (no file edits)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When:** User wants strict review and hardening **plan** before any changes.

**Do not modify files.** Only produce review output.

---

## Inputs (paste below)

**Task:** `tasks/<name>/`

**Platform summary / agent results / test quality / rubric:**

```
[paste here]
```

---

## Inspection (mandatory)

Read actual task files, benchmark summary, oracle/NOP results, logs. **Do not guess.**

---

## Review checklist

### 1. Core challenge

What must the agent understand or repair? Realistic engineering vs formatting/one-file cleanup?

### 2. Intended bugs (≥3–5)

List distinct bugs/behaviors with source locations. Do they **interact**? If &lt;3 meaningful behaviors → **too easy**.

### 3. Shallow-solution risk

Can agents pass via one line, one file, hardcoded output, stub, or artifact write? How to block?

### 4. Tests force real repair?

CLI/API rebuild, fresh temp state, independent expected values, success + failure paths?

### 5. Oracle quality

Real code fixes vs writing golden artifacts?

### 6. Instruction

WHAT without HOW? Flag bug locations, spoilers, vague reqs, agent-visible fix hints.

### 7. Frontier failure modes (≥3)

e.g. stale state, wrong ordering, skip rebuild, hardcode output, miss idempotency. If none → likely trivial.

### 8. Classify from agent results

| Band | Rule |
|------|------|
| Hard | best ≤20% OR worst ≤20% |
| Medium | worst &gt;20% and ≤60% |
| Easy | worst &gt;60% and ≤80% |
| Trivial | strong agents pass nearly all / shallow fixes |

No agent data → **“target only, not confirmed.”**

### 9. Review fixes made it easier?

Removed bugs, golden leaks, weakened tests, artifact-only oracle?

### 10. Harder but fair proposals

If too easy: state/replay/persistence, ordering, cross-module, corrupt input, idempotency, dynamic fixtures — **not** shallow edge cases only.

### 11. Verifier stability

`test.sh` bootstrap, `cd /app`, no runtime installs, no flaky timing — no `verifier_did_not_run`.

---

## Final output (required)

| Field | Value |
|-------|-------|
| **Difficulty risk** | Low / Medium / High |
| **Triviality risk** | Low / Medium / High |
| **Accepted-likely** | Yes / No |
| **What makes it hard** | … |
| **What could make it trivial** | … |
| **Required changes** (no hidden reqs) | … |
| **Needs Revision categories** | … |
| **Recommended trivial case** | Case 1 / 2 / 4 / TB3 / Harden |

**Next step:** user invokes `@prompts/trivial.md` with chosen case to implement.
