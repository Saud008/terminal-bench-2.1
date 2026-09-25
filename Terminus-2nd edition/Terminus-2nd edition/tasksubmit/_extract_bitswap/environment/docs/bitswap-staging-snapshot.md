# Staging schema

Path: /app/state/bitswap-snapshot.json

Fields:

session_id — string session name from --session.

wants_remaining — array of {cid, priority} after full replay. Each cid is a display CID (trace registry string), never canonical multihash hex. Sorted by priority descending then cid ascending.

delivered — array of {cid, peer, bytes, priority}. Grows with every block_done: one append per event. The cid field is the registered display CID from the active want at block_done when present (first registration wins on alias merge); otherwise the block_done event cid. Export sorting uses cid then peer ascending.

ledger_totals — array of {peer, cid, credit}. Each cid is a display CID string credited on the first block_done for that peer and cid pair; never canonical multihash hex. Duplicate block_done events for the same peer and display cid do not add credit again. Sorted by peer then cid.

partial_blocks — count of partial buffers still stored.

in_flight_count — count of blocks started but not completed.

Snapshot is authoritative for export. Export copies these fields without recomputing from scratch files. See /app/docs/bitswap-display-cid-rules.md for display versus canonical key rules.
