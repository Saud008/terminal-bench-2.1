# Platform rubric — relay-duel-fork-window-seal-ledger

**Task folder:** tasks/relay-duel-fork-window-seal-ledger/
**Form category:** Game (zip `games`; bash/python playtest desk)
**Written:** 2026-07-28T08:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent admits duel admit-log JSONL with ts_ms and cseq ordering, +3
Agent joins match branches on duel_id plus fork_tag per lane-fork contract, +3
Agent treats hold status 183 as non-accept for ledger export, +3
Agent applies FORFEIT precedence over RESIGN when both appear pre-accept, +3
Agent suppresses duplicate duel retransmits before fold-branches, +3
Agent shifts accept timestamps by clock_skew_ms before score banding, +3
Agent rates matches with inclusive score window end minute, +2
Agent exports only answered matches with final disposition to SQLite, +3
Agent writes match-buffer.json with match_seal before seal-ledger, +2
Agent reads TB3_FIXTURE_DIR for hidden forfeit poison scenarios, +2
Agent produces byte-stable match-ledger.sqlite on cross-run idempotent replay, +2
Agent keeps /app/bin/duelctl current after /app/lib/duelctl edits, +1
Agent leaves decoy module off seal-ledger hot path, +1
Agent sorts ledger_rows by duel_id then branch_key ascending, +2
Agent sorts admit-log by cseq only ignoring ts_ms tie order, -3
Agent exports hold-only legs into match-ledger.sqlite, -3
Agent prefers RESIGN over FORFEIT when both close the same branch, -3
Agent drops retransmit duplicates causing duplicate SQLite rows, -3
Agent ignores clock_skew_ms when rating rush versus calm, -3
Agent uses non-canonical Dockerfile base image, -5
