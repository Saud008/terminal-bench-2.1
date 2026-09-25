# Export schema

Path: argument to --output on pipeline command.

Fields:

report_version — always 1.

session_id — matches staging snapshot.

wants_remaining — identical to staging wants_remaining. Each cid is a display CID (trace registry string), never a canonical multihash hex key. Sorted by priority descending then cid ascending.

delivered — identical to staging delivered. Array of {cid, peer, bytes, priority}. One row is appended for every block_done event in trace order before export sorting. The cid field is a display CID: when an active want existed at block_done, use the registered display CID from that want entry (alias merge keeps the first registered display); otherwise use the block_done event cid. Sorted for export by cid ascending then peer ascending.

ledger_totals — identical to staging ledger_totals. Array of {peer, cid, credit}. Each cid is a display CID string from the block_done event that first credited that peer and cid pair; values are never canonical multihash hex. Credit bytes apply only once per peer and display-cid pair even when multiple block_done events occur. Sorted by peer ascending then cid ascending.

partial_blocks — identical to staging partial_blocks.

in_flight_count — identical to staging in_flight_count.

delivery_count — length of delivered array (counts every block_done delivery row, including duplicates that share a canonical block).

CID representation summary: all cid fields in this report are display CIDs per /app/docs/exchange-display-token-rules.md. Canonical keys are used only inside ingest and never written to export JSON.

Metrics export (/app/docs/exchange-metrics-export.md) is separate from pipeline export.
