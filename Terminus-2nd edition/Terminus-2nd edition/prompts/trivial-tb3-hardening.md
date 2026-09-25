# TB3 — Full hardening + AutoEval stability

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Rules: `.cursor/rules/LOCKED.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.


**When:** TB3 task needs **genuine HARD/VERY HARD** difficulty, possible **language rebuild** (Rust/Go/Java/C/C++/Zig/Bash), and **verifier stability** — without platform-infra failures.

**Target:** hard + **solvable** (~20% worst model, not 0/5 forever).

**Also load:** [`trivial-repo-wide.md`](trivial-repo-wide.md) — repository-wide contract (§1–§12).

---

## Platform evidence (paste below)

```
[paste benchmark summary, unit-test pass rates, agent failure logs]
```

---

## Step 1 — Analyze before editing

Inspect task files, agent logs, per-test pass table.

**Keep:**

- Tests agents partially solve or fail for semantic reasons  
- Cross-file reasoning, state, ordering, replay, persistence, recovery  
- Oracle/verifier path unless genuinely flawed  

**Replace / strengthen:**

- Tests all agents solve easily  
- One-function bugs, hardcoded shortcuts, shallow parser fixes  
- Tests that skip real runtime behavior  

If core logic is **shallow Python**, consider rebuild in **Rust, Go, Java, C, C++, Zig, or Bash** with full runtime behavior, persistence, CLI workflow, and verifier compatibility.

---

## Step 2 — Increase difficulty (real semantics)

- Durable state and stale-state recovery  
- Replay/idempotency across multiple runs  
- Ordering-sensitive output and merge semantics  
- Delayed-effect bugs (failure after restart/replay)  
- Cross-module dependencies  
- Corrupt partial state recovery  
- Hidden/dynamic fixtures under `tests/` only  
- Semantic invariants not solvable by grep or one-line patches  
- Multi-step workflows — fix in one subsystem affects another  

**Do not:** shallow hardening only; one obvious bug; regex-only tests; golden leaks; BUG/verifier/pytest wording in agent-visible files.

---

## Step 3 — Verifier stability (mandatory)

Fix `tests/test.sh` so it cannot produce `verifier_did_not_run`:

- `mkdir -p /logs/verifier` at start  
- Prewrite `reward.txt` to `0`  
- Minimal `ctrf.json` before early exits  
- Explicit `cd /app` before rebuild/tests  
- Never exit only because `$PWD` is `/`  
- No runtime installs  
- Pytest produces CTRF when tests start  
- Final platform reward block preserved  

---

## Step 4 — Docker / environment

- `allow_internet = false`  
- All verifier deps in `environment/Dockerfile` (pinned)  
- Toolchains on PATH (`/usr/local/bin/cargo`, `go`, `mvn`, symlinks if needed)  
- **Do not** copy `tests/`, `solution/`, hidden fixtures, expected outputs into agent image  
- Strip caches, `target/`, `.gradle/`, `__pycache__` from submission  

---

## Step 5 — Metadata (align with repo policy)

- `category = "debugging"` for repair tasks  
- `subcategories`: **always `[]`** (empty)
- Tags **≤6**  
- `difficulty` = `medium` or `hard`  
- `workdir = "/app"` for non-milestone (unless platform schema rejects — then follow platform)  
- **No `rubric.md` in task zip** unless user asks (platform rubric separate)  

---

## Step 6 — Verify loop

Iterate until all pass:

1. Static checks  
2. Docker build  
3. Oracle offline → **100%**  
4. NOP → **0%**  
5. `collapse_check.py` if available  
6. No `verifier_did_not_run`  
7. Design: strong agent **can** still solve; weak agents **mostly fail**  

**Stop before 0/5 unsolvable.**

---

## Output

- Language/stack decision (keep vs rebuild)  
- Module interaction map  
- Verifier bootstrap changes  
- Tests replaced vs kept  
- Commands + results  
- Solvability guard (not 0/5 design)  
