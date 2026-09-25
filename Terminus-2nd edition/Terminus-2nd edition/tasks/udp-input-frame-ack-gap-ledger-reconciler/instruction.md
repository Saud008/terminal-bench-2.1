The UDP input reconciler under /app already ships a two-stage udpctl ingest, staging, and export pipeline for captured client input frames; bring that existing pipeline into compliance with the contracts so replay reports match /app/docs/wire-format.md, /app/docs/ledger-contract.md, /app/docs/sim-contract.md, /app/docs/staging-contract.md, and /app/docs/replay-export.md.

udpctl ingest --bundle <path> --seed <n> processes a JSON bundle from /app/fixtures/bundles/, updates the gap ledger and sim state, and writes /app/state/replay-staging.json. udpctl export --export <path> reads that staging snapshot and emits the replay export JSON. udpctl replay runs ingest then export in one invocation.

Build the pipeline so bundled fixtures (baseline.json, wrap-u32-edge.json, dup-resend.json, out-of-order.json, loss-bitmask.json, and partial-tick-batch.json) produce reference parity for seed 7 from /app/fixtures/seeds.json. Baseline replay must show distinct client_id and state_hash when the seed changes.

Write export JSON to the exact path given by --export (for example /app/output/replay-report.json). Do not edit /app/docs/, /app/fixtures/, or /tests/.
