# Reviewer feedback — RF1 (minimal: timeouts + Linux user/password)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Reviewer asks for **timeout compliance** and/or **Unix user password** setup only. **Fix this only — do not add or remove anything extra.**

---

## Reviewer feedback (paste below)

```
[paste reviewer comments here]
```

---

## Rules (LOCKED for this prompt)

1. **Inspect** `task.toml` only (and `environment/Dockerfile` if password/user is required) before editing.
2. **Fix only** what review states:
   - All timeout fields ≤ platform max (**900s** for agent/verifier; build **600–900s** per task needs).
   - If Linux user/password is required: add minimal `RUN useradd` / `chpasswd` or documented pattern — **do not commit real passwords**; use placeholder or build-arg pattern the reviewer specifies as `()` in their note.
3. **Do not** change instruction, tests, oracle, difficulty, or unrelated Dockerfile lines.
4. **Do not** add dependencies, tests, or refactors.

---

## Timeout checklist

| Field | Max allowed |
|-------|-------------|
| `[agent] timeout_sec` | 900 |
| `[verifier] timeout_sec` | 900 |
| `[environment] build_timeout_sec` | 900 (600–900 typical) |

---

## After edits

1. Oracle + NOP if any file beyond `task.toml` / user setup changed materially.
2. Report: files touched, values before/after.

---

## Output

| Reviewer point | Valid? | File(s) | Change made |
|----------------|--------|---------|-------------|

- **Verified by execution:** yes/no
- **Intentionally not changed:** (list)
