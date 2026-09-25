Build a host-local Prometheus remote-write ingest service (`promingest`) that only accepts checksum-valid write blocks, stages admitted series on disk, and exports sealed snapshots from that staging state—never from in-memory-only writes.

## Behavioral contracts

- Listen on `127.0.0.1:9090`.
- Reject write blocks whose body CRC fails; rejected writes must not create staging files.
- Accepted writes must persist tamper-evident staging under `/app/data/ingest/<seed>.json` before any snapshot may read that seed back.
- Staging sequence starts at `1` and increments on every later admitted write for the same seed (no reset between admits).
- Preserve native histogram schema integrity (schema must not be downgraded below the admitted value; schema values of 2 or higher export as 2).
- Relabel first-wins label admission and exemplar `le` binding run only during snapshot export, not during write admission.
- Counter-reset series drop exemplars in the exported snapshot.
- Missing staging must fail closed: snapshot returns `sequence` 0 and `series` as an empty JSON array (`[]`, not `null`).

Primary artifacts:

- `/app/data/ingest/<seed>.json` — staging record after admitted writes
- `GET /api/v1/snapshot?seed=...` — sealed export bound to staging sequence and admitted series

## Reference docs and layout

Operator surfaces and layout are defined in `/app/docs/remote-write.md`, `/app/docs/native-histogram.md`, `/app/docs/exemplar-binding.md`, `/app/docs/relabel-rules.md`, `/app/docs/staging-ingest.md`, and `/app/docs/contract.md`.

## Available tools and fixtures

- `/usr/local/bin/promingest` — ingest/export service under test
- `/usr/local/bin/promenc` — encodes fixture blocks for admission checks
- `/app/scripts/reset-state.sh` — clears staging so each evaluation starts from a clean ingest directory
- `/app/scripts/start-server.sh` — starts (or restarts) the service after state changes
- Bundled fixtures under `/app/fixtures`; hidden verifier seeds may appear under `/opt/verifier-fixtures`

The experimental normalize helper is not on the write-admission or snapshot-attestation path. Do not edit `/app/docs/` or `/app/fixtures/`.
