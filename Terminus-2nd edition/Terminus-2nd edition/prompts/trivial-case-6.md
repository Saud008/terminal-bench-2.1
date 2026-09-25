# TRIVIAL Case 6 — Structural redesign (default TRIVIAL/EASY)

> **LOCKED** — Canonical Terminus prompt. Hub: `.cursor/rules/shared/WORKFLOW-MAP.mdc` · Pack: `./scripts/pack_zip.sh <name>`. Do not weaken unless the user overrides in this message.

**When:**

- Platform label **TRIVIAL** or **EASY**, or either benchmark **≥3/5**, or worst **>40%**
- **`terminus-claude-opus-4-8` 5/5 AND `terminus-gpt5-5` 5/5** (or worst model **>60%**)
- Probes in **`revise/trivial-hardening-probes.mdc`** show **FAIL** (especially Probe 1, 4, or 6)
- Second or third TRIVIAL revision on the **same slug**

**Do not:** add more report fields, more hash columns, or more pytest without **new pipeline structure**.

**Target:** **`terminus-claude-opus-4-8` ≤20%** or timeout @ 1800s — fair and solvable (`platform-preferences.mdc` §1b).

**Mandatory load:**

- `revise/trivial-hardening-probes.mdc` — run all probes; paste table
- `prompts/trivial-repo-wide.md` §13–§14
- `shared/accepted-corpus.mdc` — read **≥2** accepted tasks for **shape**, not domain clone

---

## Platform evidence (paste below)

```
[paste: `terminus-claude-opus-4-8` X/5, `terminus-gpt5-5` Y/5, per-test table, note "Case 5 already applied on <date>"
```

---

## Step 0 — Diagnose why Case 5 failed

Answer **yes/no** (evidence required):

| Question | If **yes** → |
|----------|----------------|
| Single-file patch passes **≥60%** tests? | Bugs are **sequential**, not interacting — redesign |
| New fields (hash/fingerprint/counter) added but core bugs unchanged? | **Decorative hardening** — revert field-only churn or tie fields to poison-pill |
| Hidden tests fail for **same** reason as bundled? | Add **independent** hidden failure mode |
| All bugs visible in one module (e.g. only `closure.go`)? | Split into **persist + export + validate** |
| Instruction + one doc paragraph explains full fix? | **Spec leak** — split contract; remove recipe tone from docs |
| Task is 3rd TRIVIAL on same family (merge/replay/CLI)? | Consider **new slug** / new domain — lane saturated |

---

## Step 1 — Pick ONE structural redesign (required)

Choose **one** path; implement fully — do not combine all.

### A — Two-stage pipeline (shared mutable state)

Add a **real** intermediate artifact between ingest and export:

- Stage 1: decode / normalize → write `/app/state/...` or SQLite staging table
- Stage 2: read staging → final export
- Bugs: stage 1 passes bundled; stage 2 + **cross-stage** invariants fail hidden
- Tests: stage-2-only fix must fail Probe 1; staging drift tests

**Accepted shape refs:** stateful replay tasks in `_accepted-tasks/` (journal, sequence files).

### B — Second CLI subcommand (shared ledger)

- `tool ingest` → updates ledger; `tool export` → reads ledger + inputs
- Export-only fix passes bundled; **replay / second export** fails without ingest fix
- Sequence / epoch in ledger must match export rows

### C — Poison-pill interaction (same single binary)

Keep one CLI but add **coupled** bugs:

- Fixing merge order **without** ratio mode breaks hidden fixture
- Fixing persistence **without** serialization format breaks idempotency bytes test
- **Probe 4** must pass: plausible partial fix fails hidden only

### D — New slug (lane escape)

If **≥2** Case 5/6 rounds failed and family is saturated (`tasks/` has 3+ similar):

- New domain + **different** pipeline shape (not keyword swap)
- Similarity table vs corpus — **≥2 structural** differences required

---

## Step 2 — Bug budget after redesign

| Requirement | Minimum |
|-------------|---------|
| Interacting bugs | **5+** across **4+** modules |
| Independent hidden failure | **≥2** hidden tests fail for **different** partial-fix profiles |
| Doc files cited | **≥3** in `instruction.md` |
| Behavioral tests | **~20–27** — no duplicate shallow checks |
| Distractor modules | Optional — must be named in instruction as non-authoritative |

**Forbidden bugs:** lone typo, single off-by-one, one missing null check that fixes 90% tests.

---

## Step 3 — Tests to add (replace weak ones)

| Add | Remove / replace |
|-----|------------------|
| Partial-fix profile tests (reference knows which layer is wrong) | Tests that only check new field exists |
| Cross-stage / cross-run after redesign A or B | Duplicate closure/hash tests on same data |
| `TB3_*` hidden dir with **different** failure mode than bundled | Hidden that only repeats bundled assertion |
| Idempotent byte-identity or sequence monotonicity | Grep-source or file-exists |

---

## Step 4 — Solvability + probes (LOCKED)

```bash
harbor run -a oracle -p tasks/<name> --debug
harbor run -a nop -p tasks/<name> --debug --job-name <name>-nop-$(date +%Y%m%d-%H%M%S)
```

Run **`revise/trivial-hardening-probes.mdc`** Probes 1–6. **All applicable probes PASS** before zip.

| Check | Required |
|-------|----------|
| Oracle | **1** |
| NOP | **0** |
| Probe 1 single-file | **≥40%** tests fail |
| Probe 4 almost-correct | hidden trap exists |
| Probe 6 (if 2nd+ TRIVIAL) | structural path A/B/C/D applied |

---

## Output format

1. **Why Case 5 failed** (decorative vs sequential vs spec leak)
2. **Redesign path** (A / B / C / D) + subsystem map
3. **Poison-pill / interaction map** (which partial fixes fail which tests)
4. **Probe table** (PASS/FAIL + evidence)
5. **Files changed** (minimal)
6. **Verification** — oracle/NOP; **do not claim ≤20%** until new platform eval
