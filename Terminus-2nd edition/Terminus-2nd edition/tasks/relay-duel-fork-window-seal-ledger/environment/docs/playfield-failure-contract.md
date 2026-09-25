# Playfield failure modes — relay duel match ledger

## Arena score context

Relay duel arenas derive scored match-ledger rows by correlating offline duel admit-log lanes: CHALLENGE opens, hold signals such as status 180 or 183, final 2xx accepts, and closeouts via FORFEIT or RESIGN. Each scored lane is keyed by duel_id plus fork_tag after forking.

## Playfield gate failures

| Gate | When policy is wrong |
|------|----------------------|
| fork_tag omitted from branch join | Forked lanes combine or the unanswered fork is scored |
| Hold 183 treated as accept | Hold-only matches appear as completed ledger rows |
| RESIGN wins over early FORFEIT | Pre-accept forfeit appears as a completed match in SQLite |
| Duel retransmissions not collapsed | Repeated 200 accept signals produce twin SQLite rows |
| clock_skew_ms not applied before rating | Rush versus calm band follows uncorrected epoch values |
| Score window end treated as exclusive | Last scored second inside the window is dropped |

## Observable failure modes

Double score on forked fork-tag branches, hold-only rows in match-ledger.sqlite, forfeited matches marked completed, inflated row counts after a retransmission storm, wrong score band after skew correction, and off-catalog traps that require TB3_FIXTURE_DIR admit-logs.

## Duel concept anchors

Lane fork join, hold gating, resign-forfeit precedence, retransmission collapse, skew-adjusted scoring, inclusive arena score minute, answered-match ledger filter, CHALLENGE open, RESIGN closeout, FORFEIT preemption, hold status 183, hold status 180, fork_tag fork, cseq sort key, duel_id correlation, arena rush band, calm minute bucket.
