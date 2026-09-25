# Mutation command format

Files use extension `.mut-cmd.jsonl`. One JSON object per line.

| Field | Type | Notes |
|-------|------|-------|
| mutation_id | string | Stable mutation identifier |
| partition_id | string | Target partition id from metadata |
| mutation_version | int | Monotonic version per partition |
| command | string | Mutation command name |
| issued_at | string | RFC3339 UTC timestamp |
