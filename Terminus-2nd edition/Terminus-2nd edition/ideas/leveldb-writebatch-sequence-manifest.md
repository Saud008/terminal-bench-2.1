# Task idea — leveldb-writebatch-sequence-manifest

**Status:** IMPLEMENTED — `tasks/leveldb-writebatch-sequence-manifest/`  
**Generated:** 2026-06-27  
**Complies with:** `repository-state-requirement.mdc`, `forbidden-repair-objectives-gate.mdc`

---

## Title

**leveldb-writebatch-sequence-manifest**

## Language

**Go** (primary) — single-container Debian + Go; verifier uses Python `reference_batch.py`.

## Category and subcategories

- **category:** `data-processing`
- **subcategories:** `[]`

## Target difficulty

**Hard** (design target — not confirmed until frontier agent runs show ≤80% pass rate)

## One-line capability framing

Implement the Go modules under /app/internal/ for the wbatch CLI so replay ingests LevelDB-style write batch JSONL suites into /app/state/batch-manifest.json and publish reads only that manifest to write /app/output/batch-export-report.json per /app/docs/.

## Planned interacting behaviors (6 modules)

| # | Module | Behavior agents must implement correctly |
|---|--------|------------------------------------------|
| 1 | `internal/header/parse.go` | Read `snapshot_sequence` and `initial_sequence` from db.header.json |
| 2 | `internal/batch/parse.go` | Verify per-line checksums with running sequence; handle `sequence_reset` |
| 3 | `internal/store/apply.go` | Pending buffer; `batch_commit` flush; prefix delete and single_delete on both maps |
| 4 | `internal/barrier/sequence.go` | Snapshot barrier truncates applied ops; `sequence_reset` advances checksum only |
| 5 | `internal/manifest/build.go` | Manifest fields including `snapshot_sequence`; committed keys only |
| 6 | `internal/export/publish.go` | Manifest-only publish with canonical SHA-256 digest |

Behaviors interact: direct-to-committed puts pass suite 001 but fail pending-overlay 004; checksum verification skipped still loads lines but fails tamper test; barrier always-true passes M1 but fails 003 truncation; publish re-reading suite fails manifest-only audit.

## Why not solvable by one shallow patch

- **Pending vs committed** changes manifest keys without changing header parsing.
- **Checksum sequence** depends on `sequence_reset` mid-batch — fixing only `Within` still fails hidden 101.
- **Snapshot barrier** changes `final_sequence` and key set without changing batch line parser.
- **Publish digest** requires canonical manifest body — ingest-only fixes fail export audit.

## Likely frontier-agent failure modes

- Put directly into committed map (passes 001/002, fails 004-pending-overlay).
- Skip checksum verification (passes public suites, fails tamper + hidden sequence_reset).
- Treat `sequence_reset` as moving snapshot barrier.
- Include pending keys in manifest or zero `snapshot_sequence`.
- Re-open suite WAL during publish instead of trusting manifest file.

## Tests that force real implementation repair

- `test.sh` rebuilds `wbatch` then pytest subprocess invokes `wbatch replay` and `wbatch publish`.
- `reference_batch.py` independently replays suites; no import of /app/internal.
- Public suites 001–004 plus hidden 101-sequence-reset-trap at `/opt/verifier-fixtures/`.
- Bad-checksum tamper test expects non-zero replay exit code.
- Publish tests assert digest and `exported_at_sequence` without `--suite` flag.

## Anti-hardcoding strategy

- Reference recomputation from suite bytes + header, not checked-in expected manifests.
- Hidden fixture 101 with `sequence_reset` checksum base jump.
- Manifest digest from canonical JSON body — not a static string.
- Suite 004 distinguishes pending overlay from committed snapshot.

## Oracle strategy

- Golden Go patches per milestone; `solveN.sh` copies into `/app/internal/`, `go build`.
- M2 prereq copies M1 golden; M3 prereq copies M1+M2 + publish patch.

## Milestone or non-milestone

**Milestone** — 3 steps: M1 header/batch/store; M2 barrier/manifest; M3 publish export.

## What could make this trivial and how to avoid

| Trivializer | Mitigation |
|-------------|------------|
| Broken baseline matches public fixtures | Suite 004 pending-overlay + checksum tamper test |
| Single obvious one-line fix | Six interacting modules across three milestones |
| Output-file-only oracle | CLI subprocess tests with reference replay |
| Hidden barrier edge cases | Barrier and sequence_reset documented in /app/docs/ |
