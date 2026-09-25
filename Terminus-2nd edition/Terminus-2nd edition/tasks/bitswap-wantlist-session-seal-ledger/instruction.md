Swarm-trade wantlist arena playtest

Build the swarm-trade wantlist arena playtest, an offline exchange playfield planner for wantlist admission traps, cancel-inflight traps, peer-credit scoring, and sealed session-ledger win conditions on the working baseline under `/app`. The planner loads exchange scenario packs, applies alias-merge and priority-cancel scoring, audits idle-flush and in-flight delivery traps, then seals `pipeline` / `metrics` playtest exports when the session-ledger win condition is met. There is no live arena socket and no outbound network. This is a games swarm-trade playfield playtest and sealed-ledger win-condition workflow: keep display-token policy, staging-before-export, cancel-inflight delivery, credit dedupe, idle flush, queue-head priority, staged playfield snapshots, and sealed session/metrics atlas exports aligned. It is not a software-engineering module rebuild, debugging drill, system-administration ops desk, data-processing pipeline, or build-and-dependency-management exercise.

`wantplay` is available at `/usr/local/bin/wantplay`. Playtest verbs:

```text
wantplay pipeline --log PATH --session NAME --output PATH
wantplay metrics --log PATH --session NAME --output PATH
```

`pipeline` loads one exchange scenario pack from `/app/fixtures/exchange/` (or an overlay root), writes the playfield staging snapshot at `/app/state/want-snapshot.json`, and seals session-report playtest JSON at the caller-provided `--output` path only from that staged snapshot. `metrics` seals metrics-report playtest JSON (including `queue_head_cid` from active want priority scheduling) at `--output` after the same admission path.

Playtest session and output conventions: every staging and export payload sets `session_id` to the exact `--session NAME` argument (never a hardcoded demo label when the caller passes another name). Sealed playtest JSON is written only to the `--output` path. Optional overlays use `TB3_SESSION_PREFIX` (default `tb3`), `VERIFIER_SEED`, and `TB3_FIXTURES_DIR` as documented in `/app/docs/exchange-contract.md`; when those env vars are set, callers may pass dynamic session names and dynamic outputs under `/app/output/export-{suffix}.json` or `/app/output/metrics-{suffix}.json`.

Wantlist merge, cancel-inflight delivery, peer-credit dedupe, idle flush, display-token policy, staging fields, and sealed schemas follow `/app/docs/exchange-ops-workflow.md`, `/app/docs/exchange-contract.md`, `/app/docs/exchange-trace-events.md`, `/app/docs/exchange-display-token-rules.md`, `/app/docs/exchange-staging-snapshot.md`, `/app/docs/exchange-session-export.md`, `/app/docs/exchange-metrics-export.md`, `/app/docs/exchange-cancel-inflight-guard.md`, `/app/docs/exchange-session-idle-limits.md`, `/app/docs/exchange-fixture-roles.md`, and `/app/docs/exchange-runtime-paths.md`. Idle flush that hits the session idle limit must clear partial block buffers and the corresponding `wants_remaining` entries (and zero in-flight counters). A `block_done` that completes a cancel-while-inflight transfer must still append a delivered row that preserves the original want priority.

Example playtest passes:

```text
wantplay pipeline --log /app/fixtures/exchange/001-basic-wants.jsonl --session demo --output /app/output/session-report.json
wantplay metrics --log /app/fixtures/exchange/006-priority-cancel.jsonl --session demo --output /app/output/metrics-report.json
```

Every `cid` field in staging and export rows must be a display token from the trace registry; canonical multihash hex keys must never appear in snapshot or export JSON. Do not modify `/app/docs/`, `/app/fixtures/`, or `/tests/`. Offline only.
