# BGP route flap dampening semantics

rdampctl models **Route Flap Dampening** as defined for BGP speakers: each `(peer_id, prefix)` RIB slot carries a **figure of merit** (penalty), not a generic workflow checkpoint.

## RIB slot fields

| Field | Meaning |
|-------|---------|
| `advertised` | Prefix is currently announced on the session |
| `suppressed` | Penalty reached `suppress_threshold`; route must not be re-used |
| `penalty` | Accumulated dampening figure after decay |
| `flap_count` | Count of withdraw events that accrued flap penalty |
| `stable_at_ms` | First event-time where, **after** that event's advertised-state update, penalty is below `reuse_threshold` and the slot is still withdrawn (`advertised` is false) |

## BGP UPDATE accrual rules

Dampening reacts to **BGP UPDATE** semantics:

- **Announce while not advertised** — install route; if penalty ≥ suppress threshold, mark suppressed.
- **Announce while already advertised** — attribute refresh only; must not increment flap_count or add penalty.
- **Withdraw while advertised** — remove route; add `flap_penalty` once; increment flap_count.
- **Withdraw while not advertised** — no-op.

This is not a generic cache for reapplied workflows. Penalties decay exponentially between events using each peer's `half_life_ms` from the dampening table.

## Multi-peer isolation

Each peer maintains an independent dampening table row. The same prefix learned from `edge-a` and `edge-b` tracks separate ledger keys `edge-a:198.51.100.0/24` and `edge-b:198.51.100.0/24`.

## Suppression atlas

The atlas JSONL reports **post-simulation** RIB dampening outcomes for operators: final penalty, suppression flag, flap history, and stable event-time. Rows omit quiet prefixes that never flapped and never suppressed.
