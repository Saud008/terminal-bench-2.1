# ExecID idempotency

Drop-copy replay deduplicates on ExecID tag 17 alone across the entire database. A second row with the same ExecID is ignored and must not change net positions or active_exec_ids.

Idempotency applies inside each SQLite batch transaction: duplicate ExecID in the same batch is skipped without error,
