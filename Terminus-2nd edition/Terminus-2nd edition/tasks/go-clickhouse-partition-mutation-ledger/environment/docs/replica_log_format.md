# Replica log format

Files use extension `.replica-log.jsonl`. One JSON object per line.

| Field | Type | Notes |
|-------|------|-------|
| replica_name | string | Replica identifier |
| partition_id | string | Partition being synchronized |
| lag_sec | int | Replication lag in seconds |
| last_mutation_id | string | Last applied mutation id on replica |
