# Turn scheduler

Living actors with `action_points > 0` take turns each round.

## Turn order

1. Sort by initiative descending, then name ascending (stable).
2. Pinned living actors move to the front, preserving relative order among pinned and among unpinned groups.

Dead actors (`alive: false`) are excluded.

## Per-turn flow

For each actor in turn order:

1. Skip if not alive or `action_points <= 0`.
2. Apply bleed at **start of turn** (see `/app/docs/bleed-timing.md`).
3. If hp <= 0 after bleed, emit death event and skip remaining steps for this actor.
4. If stunned: decrement action_points by 1, clear stunned, emit `stun_skip`, skip act.
5. Otherwise decrement action_points by 1 and emit `act`.

## Events

Each event includes `kind`, `actor`, and optional `damage`, `hp_after`, `bleed_after`, `ap_after` when applicable.
