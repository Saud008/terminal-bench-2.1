# TRIVIAL Case 1 — Already flagged; do not resubmit same form

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When:** Reviewer or platform **already flagged TRIVIAL**; task was resubmitted without meaningful change.

**Target:** genuinely challenging — **hard + solvable** (~20% worst model, not 0/5).

**Also load:** [`trivial-repo-wide.md`](trivial-repo-wide.md) — repository-wide contract (§1–§12).

---

## Platform evidence (paste below)

```
[paste reviewer note: "do not resubmit same form", agent stats, per-test table]
```

---

## Rules (LOCKED)

1. **Do not** resubmit with metadata-only or cosmetic changes.
2. **Remove or replace** tests agents solve too easily.
3. **Add** complex **behavior-based** tests with realistic edge cases — not format/grep-only.
4. Task must **not** pass via one-file patch, hardcoded output, regex fix, or direct artifact generation.
5. Add **interacting** requirements: persistence, replay/idempotency, ordering, corrupt partial data, cross-module logic, failure paths.
6. Requirements stay **clear and fair** — no hidden rules.

---

## Mandatory changes

| Area | Action |
|------|--------|
| Easy tests | **Replace** — agents pass 4/5–5/5 on these |
| Hard tests | **Keep** — meaningful semantic failures |
| Bugs | **4+ across 3+ modules**, interacting |
| Instruction | Rewrite if hints exist; ≤3 paragraphs; contracts in `/app/docs/` |
| Oracle | Real implementation fixes only |
| `test.sh` | Verifier-stable bootstrap (reward `0`, CTRF, `cd /app`) |

---

## Verify before resubmit

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

- Oracle **1.0**, NOP **0.0**  
- Strong agents should **not** pass all runs locally (design check)  
- **Do not resubmit** until at least not trivial/easy and verifier stable  

---

## Output

- What changed vs previous rejected version (prove it is not “same form”)  
- Tests replaced list  
- Difficulty/solvability risk assessment  
