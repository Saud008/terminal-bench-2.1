# Task idea — bbolt-bucket-tx-snapshot-exporter

**Status:** IMPLEMENTED — `tasks/bbolt-bucket-tx-snapshot-exporter/`  
**Generated:** 2026-06-29  
**Complies with:** `repository-state-requirement.mdc`, `forbidden-repair-objectives-gate.mdc`

---

## Title

**bbolt-bucket-tx-snapshot-exporter**

## Language

**Go** (primary) — single-container Debian + Go; verifier uses Python `reference_bucket.py`.

## Category and subcategories

- **category:** `data-processing`
- **subcategories:** `[]`

## Target difficulty

**Hard** (design target — not confirmed until frontier agent runs show ≤80% pass rate)

## One-line capability framing

Implement the Go modules under /app/internal/ for the bbolt CLI so replay ingests BBolt-style bucket transaction JSONL suites into /app/state/bbolt-bbolt-bbucket-manifest.json and publish reads only that manifest to write /app/output/bbolt-publish-report.json per /app/docs/.

## Planned interacting behaviors (6)

| # | Module | Behavior |
|---|--------|----------|
| 1 | `internal/header/parse.go` | Read `snapshot_tx_id`, `initial_checksum`, `bucket_name` from bucket.header.json |
| 2 | `internal/bucket/parse.go` | Verify per-record checksums with running cursor; handle `tx_id_reset` |
| 3 | `internal/store/apply.go` | Pending buffer; `tx_commit` flush; prefix delete and single_delete on both maps |
| 4 | `internal/barrier/txid.go` | Snapshot tx_id barrier; `tx_id_reset` advances checksum only |
| 5 | `internal/manifest/build.go` | Manifest with `bucket_name`, `snapshot_tx_id`, committed keys only |
| 6 | `internal/export/publish.go` | Manifest-only publish with canonical SHA-256 digest |

## Why not solvable by one shallow patch

- Direct-to-committed puts pass 001/002 but fail 004-pending-overlay.
- Skipping checksum verification passes public suites but fails tamper + hidden 101.
- Barrier always-true passes M1 but fails 003 truncation and manifest `bucket_name` fields.
- Publish re-reading suite fails manifest-only audit.

## Likely frontier-agent failure modes

- Put directly into committed map without pending/tx_commit.
- Skip checksum verification or mishandle tx_id_reset checksum cursor.
- Ignore snapshot_tx_id barrier.
- Omit bucket_name from manifest or digest body.
- Re-open replay.bucket.jsonl during publish.

## Tests that force real implementation repair

- `test.sh` rebuilds `bbolt`; pytest subprocess runs `bbolt replay` and `publish`.
- `reference_bucket.py` independent replay from suite bytes.
- Public suites 001–004; hidden 101-tx-id-reset-trap at `/opt/verifier-fixtures/`.
- Bad-checksum tamper expects non-zero replay exit.
- Publish tests match digest without `--suite` flag.

## Anti-hardcoding strategy

- Reference recomputation from suite bytes + header, not checked-in manifests.
- Hidden tx_id_reset trap with checksum base jump.
- Manifest digest includes `bucket_name` string in canonical body.
- Suite 004 pending overlay distinguishes uncommitted puts from committed snapshot.

## Oracle strategy

- Golden Go patches per milestone; `solveN.sh` copies into `/app/internal/`, `go build`.
- M2 prereq M1; M3 prereq M1+M2 + publish patch.

## Milestone or non-milestone

**Milestone** — 3 steps: M1 header/bucket/store; M2 barrier/manifest; M3 publish export.

## What could make this trivial and how to avoid

| Trivializer | Mitigation |
|-------------|------------|
| Broken baseline matches public fixtures | Suite 004 pending-overlay + checksum tamper |
| One-line fix | Six modules across txn, barrier, bucket_name, publish |
| Output-file-only oracle | CLI subprocess + reference replay |
| Hidden edge cases | All semantics documented in /app/docs/ |
