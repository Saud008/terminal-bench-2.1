# Restore import

Restore reads bundle bytes using the index sidecar. For each member, gunzip JSONL lines and import tasks into SQLite pending table.

Dedupe: when the same task id appears in multiple members, keep the last occurrence in bundle member order (higher member_id wins; within a member later lines win).

Priority: restored pending rows must use the priority field from the archived record. Retry count must not replace or derive priority.

After restore completes, manifest export reads /app/state/archive-snapshot.json plus the index to produce output; it must not rebuild manifest ordering by scanning the live queue alone.

Manifest JSON schema version 1:

seed — string
scenario — string
ordered_ids — array of task id strings after restore dedupe
priorities — object mapping task id to integer priority
retries — object mapping task id to integer retry count
