# Platform rubric — smtp-header-thread-indexer

**Task folder:** tasks/smtp-header-thread-indexer/

Agent unions every References token when linking threads per thread-index-schema.md, +3
Agent keeps InReplyTo as a single angle-bracket string without merging References at parse time, +3
Agent selects thread roots by earliest date with Message-ID tie-break per thread-index-schema.md, +3
Agent writes snapshot digest from messages_indexed_list rows only per index-snapshot.md, +3
Agent rejects missing SQLite database paths instead of silently creating empty files, +3
Agent commits message_threads in one transaction before writing snapshot and JSON export, +2
Agent deduplicates by Message-ID while preserving first-seen file order for counters, +2
Agent implements publish from /app/state/thread-index.snapshot.json without re-indexing, +2
Agent preserves exact JSON counter and list field names from the report schema, +2
Agent rebuilds mailindex with go build after editing internal Go packages, +2
Agent discovers .eml and .mbox files recursively under the mail directory, +2
Agent links threads using only the first References token, -3
Agent creates a new SQLite file when the configured thread-db path is absent, -3
Agent hashes snapshot digest from full report JSON instead of indexed list rows, -3
Agent re-runs assign or SQLite queries during publish instead of reading the snapshot, -2
Agent strips angle brackets from stored Message-ID tokens, -2
