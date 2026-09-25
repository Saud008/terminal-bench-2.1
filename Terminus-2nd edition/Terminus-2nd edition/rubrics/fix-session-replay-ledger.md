# Platform rubric — fix-session-replay-ledger

**Task folder:** tasks/fix-session-replay-ledger/
**Written:** 2026-06-25T14:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent validates FIX tag 9 body length against measured bytes before checksum, +3
Agent sorts staging snapshot by SendingTime then ClOrdID then ExecID, +3
Agent writes ingest staging as compact JSON with trailing newline, +2
Agent applies cancel exec type 4 using signed OrderQty not LastQty, +3
Agent computes per-symbol VWAP as volume-weighted average across trade fills, +3
Agent deduplicates replay on ClOrdID and ExecID pair for idempotent ingest, +2
Agent rebuilds fix-ledger binary in test harness before pytest, +2
Agent ignores merge wrap decoy for export position math, +1
Agent hardcodes positions.json without running fix-ledger export, -3
Agent patches checksum only while staging order stays file-offset, -2
Agent uses last trade price as VWAP instead of weighted average, -3
Agent double-counts rows when re-ingesting same session files, -2
Agent emits pretty-printed staging JSON with spaces after colons, -2
