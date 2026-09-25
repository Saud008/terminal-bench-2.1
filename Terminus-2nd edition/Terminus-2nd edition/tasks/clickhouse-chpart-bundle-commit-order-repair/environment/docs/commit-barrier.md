# Commit barrier

Background commit must observe:

1. Persist all merged rows for the ingest pass.
2. Set `commit_log.fsynced = 1`.
3. Only then advance `commit_log.max_block` to the highest part `max_block`.

If `fsynced` is false, `max_block_number` in the snapshot must remain `0`.

The SQLite mirror table commit_log is the authoritative barrier state for staging and export.
