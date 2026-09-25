# Trace format

Each JSONL line contains seq (integer), op (string), and op-specific fields.

Operations:

want — fields cid, priority. Adds a want entry.

merge_wants — field wants array of {cid, priority}. Merges remote peer broadcast.

cancel — field cid. Cancels a want per /app/docs/exchange-cancel-inflight-guard.md.

block_start — fields cid, peer, optional bytes. Marks block in flight.

block_part — fields cid, peer, bytes. Records partial buffer bytes.

block_done — fields cid, peer, bytes. Completes delivery, appends one delivered row (display CID rules in /app/docs/exchange-display-token-rules.md), and credits ledger at most once per peer and display-cid pair.

tick — field idle_ms. Advances session idle clock per /app/docs/exchange-session-idle-limits.md.

Events sort by seq ascending. Duplicate seq values are invalid in bundled fixtures.
