# Reviewer feedback — RF2 (fix + oracle/NOP + quality gate)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Reviewer fix is done; must **re-verify** oracle, NOP, and static/quality checks until all pass.

**Fix this only — do not add or remove anything extra** beyond reviewer items + required verification.

---

## Reviewer feedback (paste below)

```
[paste reviewer comments here]
```

---

## Rules

1. **Timeout compliance:** `[agent]`, `[verifier]`, `build_timeout_sec` ≤ **900** seconds. No value above platform max.
2. **No secrets in repo:** Do **not** paste API keys, tokens, or passwords into task files, prompts, or commits. Run local tools with env vars only.
3. Fix **only** valid reviewer blockers + edits required for oracle to match tests.
4. Do not broaden scope (no refactors, no difficulty tuning).

---

## Verification loop (mandatory)

After fixes, run until green:

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

Optional static preflight (when available):

```bash
python3 /app/scripts/harbor/run_static_checks.py --task-dir tasks/<name> --version edition_2
```

**Target:**

- Oracle reward **1.00**
- NOP reward **0.00**
- Static/quality checks: **all pass** (e.g. 11/11 if platform reports that scale)

Re-run after each fix until targets hold. Do not claim ready without evidence.

---

## Output

| Reviewer point | Valid? | File(s) | Change made |
|----------------|--------|---------|-------------|

- Commands run + results (oracle, NOP, static)
- **Verified by execution:** yes/no
