# Partition metadata format

Files use extension `.part-meta.jsonl`. One JSON object per line.

| Field | Type | Notes |
|-------|------|-------|
| part_id | string | Unique part identifier |
| table_name | string | ClickHouse table name |
| partition_key | object | Column name to string value map |
| detached | bool | True when part is detached |
| part_count | int | Number of parts in partition |

Files processed in lexicographic filename order.
