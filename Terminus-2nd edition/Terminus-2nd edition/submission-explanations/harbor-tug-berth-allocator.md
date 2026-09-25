# Submission explanations — harbor-tug-berth-allocator

**Task folder:** tasks/harbor-tug-berth-allocator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is marked hard because the harbor tug berth allocator couples six independent defects across NMEA parsing, SQLite idempotency, staging serialization, pairwise overlap math, and export reporting. Contracts in berth-contract.md, export-format.md, and idempotency.md split the rules across ingest and export stages, so fixing MMSI validation alone still leaves duplicate replays inflating accepted counts and wrong overlap totals on berths with concurrent assignments. The merge rollup helper looks authoritative but publishes maximum single-assignment dwell instead of summed pairwise intersection minutes, which passes superficial inspection on non-overlapping fixtures. Export also fingerprints a CSV summary rather than the on-disk staging snapshot bytes, so agents who only patch ingest or overlap still fail digest and hidden overlap traps.

## Solution Explanation

The oracle replaces broken Go sources in internal/nmea, internal/db, internal/staging, internal/overlap, internal/ingest, and internal/export, then rebuilds tug-berth with go build. NMEA parsing must read nine decimal MMSI digits from the VDM payload at the documented offset. Idempotency keys must include voyage_id with berth_id and arrival_utc, and duplicate rejections must increment only duplicate_rejected inside the same transaction as the failed insert. Staging must write canonically sorted JSON rows to /app/state/ingest-snapshot.json, and export must compute concurrent_overlap_minutes with pairwise interval intersection while setting staging_digest to the SHA-256 of that file's exact bytes. The decoy merge package must stay off the export hot path.

## Verification Explanation

Pytest runs twelve behavioral cases that drive tug-berth ingest and export through subprocess CLI calls against bundled and hidden JSONL fixtures under /tmp/verifier-fixtures/harbor-tug. An independent reference_nmea module simulates ingest acceptance, duplicate replay, canonical snapshot bytes, and expected berth reports so agents cannot hard-code alpha fixture output. Tests assert MMSI cross-checks, voyage-scoped idempotency, staging digest hashing from on-disk bytes, berth and assignment sort order, and that concurrent overlap equals summed pairwise minutes rather than the decoy max-dwell rollup. A rebuild case deletes the installed binary and compiles from Go sources before running export, blocking stale image binaries from masking unfixed export logic.
