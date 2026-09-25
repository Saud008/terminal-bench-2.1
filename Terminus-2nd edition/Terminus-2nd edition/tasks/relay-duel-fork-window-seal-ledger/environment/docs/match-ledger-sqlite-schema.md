# SQLite ledger schema

Table ledger_rows columns: duel_id, branch_key, answer_ts_ms, end_ts_ms, duration_sec, score_band, disposition.

Primary key (duel_id, branch_key). Rows sorted by duel_id asc then branch_key asc on publish.

Only matches with answered true and disposition completed or forfeited are written to match-ledger.sqlite.
