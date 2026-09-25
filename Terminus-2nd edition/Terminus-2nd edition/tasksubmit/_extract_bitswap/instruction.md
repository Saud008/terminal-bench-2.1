Wantlist exchange playtest

Build the wantlist exchange playtest, an offline bitswap session playfield planner for wantlist admission, cancel-inflight traps, peer-credit scoring, and sealed session-ledger win conditions on the working baseline under `/app`. The planner loads JSONL exchange scenario packs, applies alias-merge and priority-cancel scoring, audits idle-flush and in-flight delivery traps, then seals `pipeline` / `metrics` playtest exports when the session-ledger win condition is met. This is a games wantlist-exchange playtest and sealed-ledger workflow: keep display-CID policy, staging-before-export, cancel-inflight delivery, credit dedupe, idle flush, queue-head priority, staged playfield snapshots, and sealed session/metrics exports aligned. It is not a generic Go CLI engineering, libp2p module rebuild, debugging, security admission, data-processing pipeline, or CI tooling exercise.

bswapd is available at `/usr/local/bin/bswapd`. Subcommands and flags are cataloged under `/app/docs/`:

  pipeline
  metrics

`bswapd pipeline --log PATH --session NAME --output PATH` loads one exchange scenario from `/app/fixtures/bitswap/` (or an overlay root), writes the playfield staging snapshot at `/app/state/bitswap-snapshot.json`, and seals session-report playtest JSON at the caller-provided `--output` path only from that staged snapshot.

`bswapd metrics --log PATH --session NAME --output PATH` seals metrics-report playtest JSON (including `queue_head_cid` from active want priority scheduling) at the caller-provided `--output` path after the same admission path.

Wantlist merge, cancel-inflight delivery, peer-credit dedupe, idle flush, display-CID policy, staging fields, and sealed schemas follow the contracts under `/app/docs/` (`bitswap-ops-workflow.md`, `bitswap-contract.md`, `bitswap-trace-events.md`, `bitswap-display-cid-rules.md`, `bitswap-staging-snapshot.md`, `bitswap-session-export.md`, `bitswap-metrics-export.md`, `bitswap-cancel-inflight-guard.md`, `bitswap-session-idle-limits.md`, `bitswap-fixture-roles.md`, `bitswap-runtime-paths.md`).

Example playtest passes:

  bswapd pipeline --log /app/fixtures/bitswap/001-basic-wants.jsonl --session demo --output /app/output/session-report.json

  bswapd metrics --log /app/fixtures/bitswap/006-priority-cancel.jsonl --session demo --output /app/output/metrics-report.json

Every `cid` field in staging and export rows must be a display CID from the trace registry; canonical multihash hex keys must never appear in snapshot or export JSON. Optional overlays use `TB3_SESSION_PREFIX`, `TB3_FIXTURES_DIR`, and `VERIFIER_SEED` when documented in the playfield contracts. Do not modify `/app/docs/`, `/app/fixtures/`, or `/tests/`. Offline only.
