# Playtest rules contract

Geo filter level promotion scores only after a sealed playtest atlas binds token pin
rulecards, inclusive rectangular window scoring, replica lag turn caps, floor quorum
rulecards, and residual-affinity rank caps. Reject reason codes are the authoritative
playtest signals. Score-round must refuse level promotion when any mandatory rule fails.

Durable playfield state paths:
- /app/state/level-roster.json — load-level roster
- /app/state/run-meta.json — load-level run metadata
- /app/state/round-score.json — score-round ledger
- /app/output/geo-filter-playtest-atlas.json — sealed playtest atlas
