# Task idea — kafka-segment-offset-compaction-exporter

**Status:** IMPLEMENTED — `tasks/kafka-segment-offset-compaction-exporter/`  
**Generated:** 2026-06-27  
**Complies with:** `repository-state-requirement.mdc`, `forbidden-repair-objectives-gate.mdc`

---

## Title

**kafka-segment-offset-compaction-exporter**

## Language

**Go** (primary) — single-container Debian + Go; verifier uses Python `reference_segment.py`.

## Category and subcategories

- **category:** `data-processing`
- **subcategories:** `[]`

## Target difficulty

**Hard** (design target — not confirmed until frontier agent runs show ≤80% pass rate)

## One-line capability framing

Implement the Go modules under /app/internal/ for the kseg CLI so replay ingests Kafka-style compacted segment JSONL suites into /app/state/segment-manifest.json and publish reads only that manifest to write /app/output/segment-export-report.json per /app/docs/.

## Planned interacting behaviors (6)

| # | Module | Behavior |
|---|--------|----------|
| 1 | `internal/segment/parse.go` | Verify per-line checksums with running sequence; handle `epoch_bump` |
| 2 | `internal/store/compact.go` | `txn_open` buffer; puts/tombstones pending until `txn_commit` flushes compacted map |
| 3 | `internal/barrier/offset.go` | `snapshot_offset` barrier; `epoch_bump` advances checksum only |
| 4 | `internal/header/parse.go` | Read `snapshot_offset`, `initial_sequence`, `partition_id` from segment.header.json |
| 5 | `internal/manifest/build.go` | Manifest with `snapshot_offset`, `final_offset`, `partition_id`, committed keys only |
| 6 | `internal/export/publish.go` | Manifest-only publish with canonical SHA-256 digest |

## Why not solvable by one shallow patch

- Direct-to-compacted puts pass suite 001 but fail 004-pending-txn-overlay.
- Skipping checksum verification passes public suites but fails tamper test and hidden 101 epoch_bump.
- Barrier always-true passes M1 but fails 003 snapshot truncation and manifest field checks.
- Publish re-reading suite passes ingest tests but fails manifest-only export audit.

## Likely frontier-agent failure modes

- Apply puts/tombstones directly to compacted map without txn_open/commit.
- Delete tombstones immediately instead of on txn_commit.
- Ignore snapshot_offset barrier (include post-barrier keys).
- Treat epoch_bump as moving snapshot barrier.
- Re-open replay.segment.jsonl during publish.

## Tests that force real implementation repair

- `test.sh` rebuilds `kseg`; pytest subprocess runs `kseg replay` and `kseg publish`.
- `reference_segment.py` independent replay from suite bytes.
- Public suites 001–004; hidden 101-epoch-bump-trap at `/opt/verifier-fixtures/`.
- Bad-checksum tamper expects non-zero replay exit.
- Publish tests match digest without `--suite` CLI flag.

## Anti-hardcoding strategy

- Reference recomputation from segment bytes, not golden manifest files.
- Hidden epoch_bump trap with checksum base jump after barrier offset.
- Manifest digest from canonical JSON including `partition_id`.
- Suite 004 pending txn overlay distinguishes uncommitted overlay from compacted snapshot.

## Oracle strategy

- Golden Go patches per milestone; `solveN.sh` copies into `/app/internal/`, `go build`.
- M2 prereq M1; M3 prereq M1+M2 + publish patch.

## Milestone or non-milestone

**Milestone** — 3 steps: M1 segment checksums + txn compaction; M2 snapshot_offset barrier + manifest; M3 manifest-only publish.

## What could make this trivial and how to avoid

| Trivializer | Mitigation |
|-------------|------------|
| Broken baseline matches public fixtures | Suite 004 pending overlay + checksum tamper |
| One-line obvious fix | Six modules across txn, barrier, epoch, publish |
| Artifact-only verification | CLI subprocess + reference replay |
| Hidden undocumented edges | All semantics in /app/docs/segment-format.md, commit-semantics.md, snapshot-barrier.md |
