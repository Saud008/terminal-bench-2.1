# Delete gate

Delete-by-query processing uses a two-phase gate:

1. Open the inverted-index delete gate (delete_gate_open true in delete-audit.json).
2. Apply tombstones to the inverted index token postings.
3. Run doc store garbage collection only after delete_gate_open is true and inverted index tombstones are applied.
4. Set tombstones_applied true in delete-audit.json.

Doc store GC must not remove rows before the delete gate opens.

Split publish must not append manifest rows until tombstones_applied is true for all pending delete operations queued before that publish.

Search excludes any doc_id present in the tombstone table once tombstones_applied is true.
