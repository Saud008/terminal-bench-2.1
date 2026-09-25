When a split occurs during publish, the journal layer appends ParentPivot to /app/state/split_journal.jsonl before persisting the right child page into /app/state/page_registry.json

RightPage journal entries follow the persisted page. Split event ordering is enforced in the journal crate alongside crash replay.

Crash replay journal files use split_seq to deduplicate split markers on replay.
