# SQLite CDR schema

Table cdr_rows columns: call_id, branch_key, answer_ts_ms, end_ts_ms, duration_sec, billing_tier, disposition.

Primary key (call_id, branch_key). Rows sorted by call_id asc then branch_key asc on publish.

Only dialogs with answered true and disposition completed or canceled are written to cdr.sqlite.
