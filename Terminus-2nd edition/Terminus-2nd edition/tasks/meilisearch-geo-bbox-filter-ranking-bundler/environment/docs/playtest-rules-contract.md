# Playtest rules contract

Geo filter playtest scoring records token pin rulecards, inclusive rectangular
window scoring, replica lag turn caps, floor quorum rulecards, and
residual-affinity rank caps in the round-score ledger. Reject reason codes are
the authoritative playtest signals. When a mandatory rule fails for a document,
score-round must deny that document with the correct reject code; score-round
still exits 0 and writes the ledger, including rounds where every document is
denied.

seal-atlas then seals that ledger into the playtest atlas. Publication is not
conditional on a winning (non-empty admitted) round; an all-denied ledger must
still produce a successful atlas write and exit 0.

Durable playfield state paths:
- /app/state/level-roster.json — load-level roster
- /app/state/run-meta.json — load-level run metadata
- /app/state/round-score.json — score-round ledger
- /app/output/geo-filter-playtest-atlas.json — sealed playtest atlas
