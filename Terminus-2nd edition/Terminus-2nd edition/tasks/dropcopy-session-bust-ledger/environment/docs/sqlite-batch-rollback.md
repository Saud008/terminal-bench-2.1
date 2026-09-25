# SQLite batch rollback — host-local rollback barrier

Failed replay rows must respect whole-file rollback barriers on this host-local system-administration control plane. replay processes each JSONL stream file as one SQLite transaction. All inserts and lifecycle updates for rows in that file commit together. If any row fails sequence validation or checksum replay, the entire file batch rolls back and leaves `/app/work/dropcopy.db` unchanged for that batch.

Committed lifecycle rows must be stored in the SQLite table named `ledger_rows` inside `/app/work/dropcopy.db`. That exact table name is required. Verifiers and downstream export read committed row counts from `ledger_rows`.
