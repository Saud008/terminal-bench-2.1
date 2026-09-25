# Platform rubric — bitswap-wantlist-session-seal-ledger

**Task folder:** tasks/bitswap-wantlist-session-seal-ledger/
**Category:** games (CodeBuild blocks debugging/software-engineering; platform form = Game)
**Written:** 2026-07-30T00:30:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent merges alias wants onto one canonical entry keeping the maximum priority, +3
Agent tombstones canceled wants so later merges cannot resurrect a lower priority, +3
Agent appends one delivered row per block_done and credits ledger_totals only on the first block_done per peer and display CID, +3
Agent emits display CID strings in staging and export cid fields never canonical multihash hex, +3
Agent clears partial_blocks and wants_remaining together when an idle tick reaches the session idle limit, +3
Agent records cancel-inflight block_done deliveries that preserve the original want priority, +3
Agent writes staging snapshot at /app/state/want-snapshot.json with the contract schema before export, +2
Agent exports session and metrics JSON only from that staging snapshot into the caller --output path, +2
Agent sets metrics queue_head_cid from active wants_remaining by priority then cid ordering, +2
Agent leaves /app/docs/, /app/fixtures/, and /tests/ unmodified, +1
Agent writes canonical multihash hex into export ledger_totals or delivered cid fields, -3
Agent skips delivered append on cancel-inflight block_done or zeroes the delivered priority, -3
Agent double-credits ledger_totals on duplicate block_done for the same peer and display CID, -3
Agent resurrects a canceled want via merge at lower priority than the tombstone, -3
Agent leaves partial_blocks or wants_remaining populated after an idle_ms tick that exceeds the limit, -3
Agent publishes export by recomputing from scratch manifests bypassing /app/state/want-snapshot.json, -2
Agent edits /app/docs/, /app/fixtures/, or /tests/ to pass verification, -2
