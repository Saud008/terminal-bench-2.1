# Reviewer feedback — RF6 (triage + pushback message)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** **Before any edits** — decide what to fix vs push back. Use when feedback may expose the solution or trivialize the task.

**Do not implement reviewer feedback blindly.**

---

## Reviewer feedback (paste below)

```
[paste reviewer feedback here]
```

---

## Step 1 — Triage (no file edits yet)

Inspect actual task files. Load Terminus rules: `reviewer/REVIEWER-RULES.mdc`, `shared/anti-trivial.mdc`, `shared/runtime-verifier.mdc`, `zip/ZIP-RULES.mdc`.

For **each** comment classify:

| Comment | Class | Exact file | Problem | Safest fix | Trivializes? |
|---------|-------|------------|---------|------------|--------------|
| … | Valid blocker / Valid careful / Outdated / Needs clarification | | | | yes/no |

**Invalid / push back if feedback:**

- Adds solution hints to `instruction.md`  
- Adds a **fix checklist** or **test mirror** to instruction because of “instruction issues” (use `/app/docs/` + tests instead)  
- Exposes exact bug files or fix steps  
- Turns hidden reasoning into a checklist  
- Weakens tests or removes anti-cheat  
- Converts implementation repair into artifact writing  
- Conflicts with `allow_internet = false` or latest rules  

**Hidden behavior:** add only short **contract-level** sentence in `/app/docs/` — no exact bug, file, or test case names.

---

## Step 2 — Output triage summary

- **Feedback to fix** (list)  
- **Feedback to push back on** (list + reason)  
- **Feedback for softer contract wording** (list)  
- **Would applying all feedback exactly make task trivial?** yes/no + why  

---

## Step 3 — Fix valid blockers only

After user confirms (or implicit proceed): apply fixes using **`reviewer-feedback-4.md`** or **`reviewer-feedback-3.md`** as appropriate. Oracle + NOP after behavior/test changes.

---

## Step 4 — Reviewer pushback message (when needed)

Write a **short professional** response if some feedback should not be applied exactly.

**Tone:** respectful, clear, not defensive.

**Include:**

- What you agree to fix  
- What is outdated, invalid, or too solution-revealing  
- Why applying that part exactly would reduce difficulty  
- Safer contract-level or verifier-only alternative  
- Why task remains fair, aligned, and non-trivial  

Do not attack the reviewer. Do not say “you are wrong.” Use file/rule evidence.

---

## Optional template

```text
Thank you for the review. I will address the following in the next revision:
- [accepted fixes]

I am not applying [item] as written because [contract/fairness/triviality reason].
Instead I will [safer alternative], which preserves [difficulty/fairness property].
```
