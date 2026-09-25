# Task idea — sqlite-wal-frame-checkpoint-exporter

**Status:** IDEA ONLY (not implemented — CREATE phase required before zip)  
**Generated:** 2026-06-29  
**Complies with:** `repository-state-requirement.mdc`, `forbidden-repair-objectives-gate.mdc` (implement/build framing, no repair slug)

---

## Title

**sqlite-wal-frame-checkpoint-exporter**

## Language

**Go** (primary) — single-container image with Debian bookworm-slim + Go toolchain; verifier uses Python reference only.

## Category and subcategories

- **category:** `data-processing`
- **subcategories:** `[]`

*(Platform blocks `debugging` and `software-engineering`; work is WAL/DB backend semantics framed as manifest export capability.)*

## Target difficulty

**Hard** (design target — not confirmed until frontier agent runs show ≤80% pass rate)

## One-line capability framing (instruction opening)

Implement the Go modules under /app/internal/ for the walframe CLI so ingest-wal replays SQLite WAL frame logs into /app/state/wal-manifest.json and publish reads only that manifest to write /app/output/wal-export-report.json per /app/docs/.

## Planned interacting behaviors (6 modules)

| # | Module | Behavior agents must implement correctly |
|---|--------|------------------------------------------|
| 1 | `internal/wal/frame.go` | Parse WAL frames (page write, commit, checkpoint, salt); verify frame checksums with running salt |
| 2 | `internal/page/materialize.go` | Apply page images in frame order; page size from DB header; ignore uncommitted transactions |
| 3 | `internal/checkpoint/barrier.go` | Stop materialization at checkpoint record; manifest max_frame and backfill rules |
| 4 | `internal/manifest/build.go` | Emit manifest JSON: pages touched, checksums, commit boundaries, checkpoint generation |
| 5 | `internal/export/publish.go` | Two-stage publish: read manifest only; never re-open WAL during export |
| 6 | `internal/header/parse.go` | SQLite DB header page size + WAL salt bootstrap before first frame |

Behaviors interact: wrong salt breaks checksum on frame 2+; wrong commit handling passes single-frame tests but fails multi-transaction bundles; checkpoint barrier wrong exports pages past checkpoint; publish re-reading WAL fails audit isolation test.

## Why not solvable by one shallow patch

- Frame checksum depends on **salt state** across the whole WAL — fixing only page copy ignores commit boundaries.
- **Checkpoint barrier** changes which pages belong in manifest without changing frame parser output on early frames.
- **Publish** must be isolated from ingest — partial golden on export alone still fails two-stage audit test.
- **Multi-transaction** bundles need commit marker handling; single-frame public fixture is insufficient alone (hidden multi-commit WAL at /opt/verifier-fixtures/).

## Likely frontier-agent failure modes

- Increment `duplicate_suppressed`-style mistake: count checkpoint frames as pages or treat every frame as committed.
- Checksum without salt rotation after checkpoint record.
- Materialize pages before commit marker (dirty read).
- Export re-parses WAL instead of manifest (passes ingest tests, fails publish-only audit).
- Wrong page size (assumes 4096 instead of reading header).

## Tests that force real implementation repair

- `test.sh` rebuilds `walframe` then **pytest subprocess** invokes `walframe ingest-wal` and `walframe publish`.
- `reference_wal.py` independently replays same WAL bytes; no import of /app/internal.
- Bundled fixtures: single-page WAL, multi-commit WAL, checkpoint-truncated WAL.
- **Two-stage audit:** write synthetic manifest to disk, call publish only, assert export matches reference from manifest bytes.
- **Hidden fixture** (image `/opt/verifier-fixtures/`, not in zip): salt-change mid-WAL.
- **VERIFIER_SEED** mutates page number in generated WAL append test.
- **Partial golden traps:** only frame.go golden still fails checkpoint bundle and publish audit.

## Anti-hardcoding strategy

- Reference recomputation from WAL bytes + header, not expected JSON files in repo.
- Per-run UUID suffix tags in generated WAL lines (hidden mixed-commit builder).
- Protected SHA256 on public fixture bytes.
- Publish audit injects synthetic skipped_pages into manifest — catches hardcoded export templates.

## Oracle strategy

- `solution/golden_*.go` patches per module; `solve.sh` copies into /app/internal/, `go build`, smoke `ingest-wal` on bundled checkpoint fixture.
- Milestone oracles chain prerequisites (M2 copies M1 golden + policy patch; M3 copies M1+M2 + export patch).
- No echo-only output files — oracle builds and runs CLI.

## Milestone vs non-milestone

**3 milestones** (recommended — matches influx/etcd depth without one-shot overwhelm):

| Milestone | Scope |
|-----------|--------|
| M1 | Frame parse + salt checksum + page materialize + commit boundaries |
| M2 | Checkpoint barrier + manifest.json schema |
| M3 | Publish-from-manifest + hidden salt-trap + full pipeline |

## What could make this trivial — and how to avoid it

| Trivial risk | Avoidance |
|--------------|-----------|
| Single-frame public WAL only | Multi-commit + checkpoint-truncated bundles in catalog |
| Export rereads WAL | Mandatory publish-only audit test with synthetic manifest |
| Agents patch one file | Partial-module trap tests + 6-module docs cross-reference |
| Hidden edge in wording only | All rules in /app/docs/wal-frame-format.md, checkpoint-barrier.md with explicit salt/commit semantics |
| Oracle writes JSON directly | Oracle only patches Go; tests always subprocess CLI |

## Uniqueness vs corpus

Distinct from `influx-line-protocol-retention-compactor` (LP ingest), `etcd-lease-watch-revoke-ledger-replay` (lease JSONL), `wiredtiger-checkpoint-eviction-txn-pin-repair` (repair slug, different engine). WAL frame + salt + checkpoint manifest is a new lane.

## Next steps (CREATE — not done)

1. `tasks/sqlite-wal-frame-checkpoint-exporter/` scaffold with working baseline binary stub.
2. `repository_state_gate.py --pack-gate` → 7/7 PASS.
3. Docker oracle/NOP → 1.0 / 0.0 per milestone.
4. `./scripts/pack_zip.sh sqlite-wal-frame-checkpoint-exporter --milestone`
