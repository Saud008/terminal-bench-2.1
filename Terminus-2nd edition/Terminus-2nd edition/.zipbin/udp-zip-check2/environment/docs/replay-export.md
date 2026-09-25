# Replay export schema

`udpctl replay --export <path>` writes JSON to the exact `<path>` provided (example: `/app/output/replay-report.json`):

```json
{
  "bundle_id": "string",
  "seed": 0,
  "client_id": 0,
  "state_hash": "hex",
  "ledger": {
    "playhead": 0,
    "gaps": [{"start": 0, "end": 0}],
    "duplicate_acks": 0,
    "peer_loss_gaps": [{"start": 0, "end": 0}],
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

Seeds in `/app/fixtures/seeds.json` mutate `client_id` and add `(seed * 17)` to each packet's `frame_seq` before parsing.

`ledger.gaps` and `ledger.peer_loss_gaps` follow different in-memory update rules before export. **Received-sequence gaps** (`ledger.gaps`) are recomputed from the full `seen` set after each frame; **peer-loss gaps** (`ledger.peer_loss_gaps`) append decoded tuples per frame and are held until export. Both fields run one export-time range merge when writing this JSON. See `/app/docs/ledger-contract.md` (**Received sequence gaps** and **Peer loss gaps**).
