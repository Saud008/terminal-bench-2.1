# SP — Hard task create & revise (Claude 0% + repo-wide quality)

> **LOCKED companion** to `shared/platform-preferences.mdc` **§1b**, `prompts/trivial-case-6.md`, and `prompts/trivial-repo-wide.md`.  
> **Use for:** new tasks that should land **HARD** with **Claude 0/N** while staying **acceptance-clean**; revisions when agents pass too easily or when partial-pass exposes spec gaps.

**Pack:** `./scripts/pack_zip.sh <name>` → `tasksubmit/<name>.zip`  
**Paths:** live tree `tasks/<name>/` (sync from `tasksss/` before zip if needed)

---

## When to use

| Mode | Trigger |
|------|---------|
| **Create** | New task under `tasks/<name>/` — target **hard**, **Claude 0% OK**, oracle/NOP clean |
| **Revise (too easy)** | Platform **TRIVIAL/EASY**, agents **4–5/5**, or one-file patch passes → Case 5 repo-wide hardening |
| **Revise (too unfair)** | Agents **0%** but **same test** fails for everyone with high partial pass → `@prompts/hard.md` Case 1 (fix docs, do not ease) |
| **Revise (Claude timeout 0%)** | Claude **0/N** with oracle **100%** — **no change needed** for difficulty; only fix submission quality gaps |

**Load always:**

- `shared/platform-preferences.mdc` §1b–§1c (agent timeout vs submission quality; decorative hardening)
- `prompts/trivial-case-6.md` + `prompts/trivial-repo-wide.md` (§1–§14)
- `revise/trivial-hardening-probes.mdc` — **mandatory before zip**
- `shared/accepted-corpus.mdc` — read **≥2** `tasks/_accepted-tasks/` for stack shape
- `create/creation-rules.mdc`, `shared/anti-trivial.mdc`, `shared/first-pass-blueprint.mdc` §0–§3

---

## Difficulty target (LOCKED — reconcile 0% types)

| Outcome | Verdict | Action |
|---------|---------|--------|
| **Claude 0/N**, GPT low, oracle **1**, NOP **0**, fair docs | **Desired HARD** | Submit; do **not** weaken to lift Opus 4.8 |
| **Claude timeout** at `[agent] timeout_sec = 1800` | **Valid hardness** | Keep default timeout; deepen modules, not verifier |
| **All agents 0%**, **same** test, **89%+** on others | **Unfair spec** | Fix `/app/docs/` + `instruction.md` (`hard-case-1.md`) |
| **Either agent 4–5/5** (`terminus-claude-opus-4-8` / `terminus-gpt5-5`) | **TRIVIAL risk** | Case 6 + **probes** (`revise/trivial-hardening-probes.mdc`) |
| **5/5 after Case 5** | **Decorative hardening** | **Case 6** structural redesign (`trivial-case-6.md`) — not more fields |
| **Worst model >80%** | **Not accepted** | Case 6 or new slug; poison-pill + persistence traps |

**Mantra:** *Claude may finish at **0%**; agents may not finish in 1800s; every upload must still be oracle-clean, spec-fair, and zip-valid.*

---

## Copy-paste invoke — CREATE

```text
@prompts/sp-hard-create-revise.md
CREATE tasks/<new-name>/

Follow SP hard create mode in prompts/sp-hard-create-revise.md in full.
Read ≥2 tasks/_accepted-tasks/ (closest Go/Rust CLI). Scan tasks/, tasksubmit/, tasksss/ for duplicates.

Target: `terminus-claude-opus-4-8` at 0/N full reward is OK if fair + solvable.
Stack preference: Go or Rust, single-container, difficulty hard, codebase_size small (20+ meaningful env files).

Implement A→H per create/new-task-pipeline-A-H.mdc. Do not stop at ideas-only.
```

---

## Copy-paste invoke — REVISE

```text
@prompts/sp-hard-create-revise.md
REVISE tasks/<name>/

Platform summary (if any):
<paste Difficulty, Status, Agent Performance, Unit Tests Results>

Follow SP hard revise mode in prompts/sp-hard-create-revise.md.
Auto-route: TRIVIAL/EASY → Case 5 + probes; **5/5 after Case 5** → Case 6; 0%-forever one test + partial pass → hard Case 1; Claude 0% + oracle OK → quality-only.
Edit in place. Oracle 1 + NOP 0 before zip. Paste probe table from trivial-hardening-probes.mdc.
```

---

## Agent workflow (mandatory)

### Phase 0 — Corpus & similarity

1. `ls tasks/`, `tasks/_accepted-tasks/`, `tasksubmit/`, `tasksss/` — block slug/family duplicates.
2. Read **≥2** accepted tasks — copy **structure** (Dockerfile, `test.sh`, `task.toml`, oracle), not domain.
3. Similarity table: proposed task vs nearest neighbor — **≥2 structural differences**.

### Phase 1 — Subsystem map (before any code)

From `trivial-case-6.md` Step 1 — list every layer in `environment/`:

| Layer | Must interact for hard tasks |
|-------|------------------------------|
| Parse / validate | schema, CLI paths, env overrides (`TB3_*`) |
| Core logic | merge, precedence, transforms, closure math |
| State / persistence | ledger, journal, sequence, epoch, cache, fingerprint |
| Serialization | compact JSON, key order, trailing newline, audit hash |
| Execution | rebuild in `test.sh`, subprocess CLI |
| Reporting | stderr markers, export paths per `/app/docs/` |

**Required:** **≥4 bugs** across **≥3 modules** — fixing one layer still fails independent reference or cross-run checks.

### Phase 2 — Design for Claude Opus 4.8 (fair — primary benchmark)

Per `platform-preferences.mdc` §1b + **Claude-primary** note:

**Why Claude, not GPT:** GPT-5.5 is hard to hold at ≤20%; **`terminus-claude-opus-4-8`** is the **design target**. GPT may still pass — OK if Claude is 0% / ≤20% / times out.

**Claude behavior:** reads **whole task** (instruction + `/app/docs/`) then implements. Timeout pressure = **scope**, not cheating:

| Do | Do not |
|----|--------|
| Keep **`[agent] timeout_sec = 1800`** (platform default) | Raise agent timeout to avoid timeout labels |
| ≥4 bugs across ≥3 modules; multi-doc `/app/docs/*.md` | One-file typo; grep-the-source passes |
| Stateful replay (ledger, journal, cache, epoch) | 60–80 pytest CLI replays (verifier risk) |
| ~**18–25** behavioral tests + independent reference | Hide rules in tests only |
| Go/Rust rebuild in agent path | Slow verifier / runtime installs |
| 20+ **meaningful** env files | Filler modules for `codebase_size` |

**Timeout = valid hardness** when Claude hits 1800s after reading + partial fix — **do not weaken** if oracle **1**, docs fair, NOP **0**.

Every tested behavior → `instruction.md` **or** doc path cited in instruction.

### Phase 3 — Implement (create) or reconstruct (revise)

**Create:** `tasks/<name>/` only — `instruction.md`, `task.toml`, `environment/`, `solution/solve.sh`, `tests/test.sh`, `tests/test_outputs.py`.

**Revise too easy (Case 5):**

1. Per-test triage — remove/replace tests that pass after single-file patch.
2. Add traps: idempotent replay, fingerprint change, mutated hidden fixtures, cross-module invariants (`trivial-repo-wide.md` §3–§8, §13).
3. Independent `reference_*` in pytest — no grep-only, no static golden in `environment/`.
4. Run **`revise/trivial-hardening-probes.mdc`** — all applicable probes PASS.

**Revise still 5/5 after Case 5 (Case 6):**

1. Diagnose decorative vs sequential bugs (§13 `trivial-repo-wide.md`).
2. Pick **one** structural path: two-stage pipeline, second CLI + ledger, poison-pill only, or new slug.
3. **Do not** add more hash/fingerprint fields without new interaction.
4. Probes 1, 4, 6 must PASS before zip.

**Revise unfair (hard Case 1):**

1. Build per-test pass table from platform summary.
2. Fix **only** spec/test alignment — one sentence in `/app/docs/` often enough; **no** test weakening.

### Phase 4 — Harness & oracle (every submit)

- `tests/test.sh`: seed reward `0`, no runtime installs, rebuild before pytest, Harbor ending `if [ $? -eq 0 ]` — nothing after `fi`.
- Oracle: offline G-025; patches real source + rebuild — no hardcoded golden-only writes.
- `[agent] timeout_sec = 1800`, `[verifier] timeout_sec = 900`, `allow_internet = false`.

### Phase 5 — Verify (evidence required)

```bash
# Prefer harbor; if Desktop Docker mount fails, Docker from /tmp copy:
oracle → reward 1
NOP → reward 0
./scripts/pack_zip.sh <name>
```

### Phase 6 — Trivial hardening probes (LOCKED — before zip)

Run **`revise/trivial-hardening-probes.mdc`**. Paste probe table in reply.

| Probe | Block zip if |
|-------|----------------|
| 1 Single-file | <40% tests fail under one-file fix |
| 2 Persistence | cross-run passes without persistence fix |
| 4 Almost-correct | no hidden-only failure under partial fix |
| 6 Second+ TRIVIAL | no Case 6 structural change |

If Probes 1+4 FAIL after Case 5 edits → **Case 6**, not another doc paragraph.

Report §0 A–E from `first-pass-blueprint.mdc`. **Do not claim ready** without oracle/NOP + probe table.

---

## Output format (agent reply)

1. **Mode:** CREATE or REVISE + route (Case 5 / **Case 6** / hard Case 1 / quality-only)
2. **Subsystem map** + bug interaction (why one-file patch fails)
3. **Probe table** — Probes 1–6 PASS/FAIL (`trivial-hardening-probes.mdc`)
4. **Claude 0% rationale:** fair hard vs spec bug (if applicable)
5. **Files changed** (minimal list)
6. **Verification table:** Oracle, NOP, zip path
7. **Upload form:** canonical base **Yes/No** + actual `FROM` line
8. **Difficulty:** target HARD — confirm only after **new** platform agent eval

---

## Forbidden

- Weaken tests or instruction to lift Claude off 0% when task is fair
- Trivializing hints (bug file names, golden outputs in env)
- Manual `zip -r` — use `pack_zip.sh` only
- Apt version pins on bookworm (`tmux`, `asciinema` by name only)
- Claim **1/5** or **0/5** confirmed without platform re-eval after edits
- **Decorative hardening** — new output fields / hash columns without poison-pill interaction (§1c)
- Zip when **trivial-hardening-probes** FAIL
