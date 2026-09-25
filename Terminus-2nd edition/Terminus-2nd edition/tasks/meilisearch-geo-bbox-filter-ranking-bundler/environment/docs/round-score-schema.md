# Round score ledger

/app/state/round-score.json:
- run_id, level, load_seq, shard
- admitted [{doc_id,lon,lat,affinity,admit_rank}]
- denied [{doc_id,deny_reason}]
- admitted_count, denied_count

admitted may be empty (admitted_count == 0) when every document is denied.
That is still a valid ledger for seal-atlas.

Reject precedence: blocked_pin > blocked_bbox > blocked_replica_lag > blocked_doc_floor > blocked_admit_cap.
