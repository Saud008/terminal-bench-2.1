# Queue priority

Pending tasks in SQLite carry priority as a separate column from retry.

Lower priority integer values run before higher values when dequeuing.

On restore, priority must come from the archived JSONL priority field. Mapping retry count into priority is incorrect even when numeric values coincide on some rows.

Dequeuing for verification uses ORDER BY priority ASC, id ASC.
