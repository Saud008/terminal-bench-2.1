# Staging contract

`udpctl ingest` writes `/app/state/replay-staging.json` after processing every packet in the bundle. `udpctl export` reads that file and produces the final replay report JSON.

## Staging file schema

```json
{
  "bundle_id": "string",
  "seed": 0,
  "client_id": 0,
  "ledger_raw": {
    "playhead": 0,
    "gaps_raw": [[0, 0]],
    "peer_loss_raw": [[0, 0]],
    "duplicate_acks": 0,
    "frames_received": 0
  },
  "sim": {
    "tick": 0,
    "accumulator": 0,
    "mix": 0,
    "inputs_applied": 0
  }
}
```

## Ingest responsibilities

- Parse and mutate frames per `/app/docs/wire-format.md` and `/app/docs/replay-export.md`.
- Maintain ledger state per `/app/docs/ledger-contract.md` (recompute received gaps after each frame; append peer-loss tuples without export-time merge).
- Apply sim inputs per `/app/docs/sim-contract.md`.
- Persist **raw** gap tuples in `ledger_raw.gaps_raw` and **raw** peer-loss tuples in `ledger_raw.peer_loss_raw`. Do **not** normalize `(start, end)` pairs when `start > end`. Do **not** merge ranges in staging.
- Overwrite `/app/state/replay-staging.json` atomically at the end of a successful ingest.

## Export responsibilities

- Read `/app/state/replay-staging.json` produced by the matching ingest run.
- Run **one** export-time merge on `ledger_raw.gaps_raw` and **one** on `ledger_raw.peer_loss_raw` (same algorithm as `/app/docs/ledger-contract.md` Stage 2).
- Compute `state_hash` from staged `sim` and `client_id` with the ingest `seed`.
- Write the replay export schema from `/app/docs/replay-export.md`.

Export must not re-parse bundle packets. It must use staged ledger and sim snapshots only.
