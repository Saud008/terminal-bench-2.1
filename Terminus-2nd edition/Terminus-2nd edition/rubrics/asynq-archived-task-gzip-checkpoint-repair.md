# Platform rubric — asynq-archived-task-gzip-checkpoint-repair

**Task folder:** tasks/asynq-archived-task-gzip-checkpoint-repair/

Agent rebuilds archctl from /app Go sources before subprocess CLI verification, +2
Agent flushes each gzip member footer before recording compressed_size in the index checkpoint, +3
Agent writes staging snapshot at /app/state/archive-snapshot.json with ordered task ids, +3
Agent restores duplicate task ids with last-member-wins semantics across gzip members, +3
Agent restores archived priority separately from retry count into pending rows, +3
Agent purges archived rows using UTC RFC3339 cutoff plus configured retention skew, +3
Agent exports manifest ordered_ids from the staging snapshot not a live queue scan alone, +3
Agent keeps the first complete gzip member readable when a later member is partial, +3
Agent matches exported manifest fields to an independent archive walker reference, +2
Agent records compressed_size excluding gzip footer bytes so members fail footer checks, -3
Agent restores first duplicate id across members instead of last-win body, -3
Agent copies retry into pending priority on restore, -3
Agent purges using local timezone or ignores retention skew_ms, -3
Agent builds manifest ordered_ids from live pending only bypassing archive-snapshot.json, -3
Agent rejects the whole bundle when a trailing member is partial, -3
