# Reviewer feedback — RF5 (standard fix + difficulty recheck)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When to use:** Reviewer feedback paste with explicit file-mapping and post-edit difficulty checklist.

---

## Reviewer feedback (paste below)

```
[paste reviewer feedback here]
```

---

## Rules

1. **Inspect** actual task files before editing.  
2. Map each comment → exact file(s).  
3. Fix **only** reviewer issues and direct blockers.  
4. **Do not** rewrite unrelated working parts.  
5. **Do not** add services/deps/complexity unless required.  
6. **Do not** simplify into trivial task.  

**Keep:**

- Instruction concise, realistic, absolute paths  
- Tests aligned with instruction; behavior-based (not grep-only unless task requires)  
- Oracle deterministic, real fixes (not artifact-only)  
- Milestone layout: `steps/milestone_N/` if milestone task  
- `task.toml`: `allow_internet = false`, `workdir = "/app"`  
- `tests/test.sh`: no runtime installs; reward `0`/`1` at end  
- Verifier deps in `environment/Dockerfile`  

**Rubric:** Platform rubric is separate — **do not add `rubric.md`** to task zip unless user explicitly asks (repo policy). If reviewer mentions rubric format, verify platform rubric elsewhere; do not weaken local tests to match rubric hints.

---

## After editing — difficulty recheck

Confirm still non-trivial:

- ≥5 interacting bugs/behaviors (or ≥3 for revisions per lifecycle)  
- Tests require real implementation repair  
- Oracle does not only write expected artifacts  
- Instruction does not reveal bug locations or solution steps  
- If a test removed: replace with valid behavior test unless truly invalid  

---

## Verification

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

---

## Output

- What reviewer issue was fixed  
- Which files changed  
- What exact change was made  
- What checks were run  
- **Verified:** yes/no (oracle 1, NOP 0)  

Do not claim ready/pass/accepted without local oracle and verifier runs.
