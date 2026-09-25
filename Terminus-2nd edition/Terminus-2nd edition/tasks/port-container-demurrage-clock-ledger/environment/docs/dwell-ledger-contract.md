# Dwell ledger contract

run-dwell-ledger advances the yard dwell clock and materializes ledger artifacts.

## Outputs

| Path | Content |
|------|---------|
| /app/work/dwell-ledger.json | scenario, engine, clock_pass, ledger_digest, container_count |
| staged_dwell table | per-container dwell and tier totals |

## clock_pass

Each successful run-dwell-ledger increments clock_pass in /app/state/clock-pass.json. load-yard resets clock_pass to zero.

## ledger_digest

ledger_digest is an eight-hex-character SHA-256 prefix over sorted container tier totals and clock_pass. Tests compare digest stability on stable reruns.

## Preconditions

yard.db must exist from prior load-yard. run-dwell-ledger reads yard_meta, containers, gate_events, contracts, holds, closures, and tariffs.
