# Round score ledger

/app/state/round-score.json:
- run_id, level, load_seq, shard
- admitted [{doc_id,lon,lat,affinity,admit_rank}]
- denied [{doc_id,deny_reason}]
- admitted_count, denied_count

Reject precedence: blocked_pin > blocked_bbox > blocked_replica_lag > blocked_doc_floor > blocked_admit_cap.
