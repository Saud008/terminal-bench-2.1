# Platform rubric — go-rabbitmq-quorum-queue-raft-inspector

**Task folder:** tasks/go-rabbitmq-quorum-queue-raft-inspector/

Agent replays quorum queue Raft logs with term and index ordering, +3
Agent applies snapshot truncation exclusive at last_included_index, +3
Agent tracks leader election transitions across quorum terms, +3
Agent excludes uncommitted tail queue rows above commit_index, +3
Agent reconciles replica membership after same-term config changes, +3
Agent writes raft-staging.json with replay_digest seal fields, +2
Agent exports committed-queue-state.jsonl sorted by queue_id, +2
Agent requires positive raft_seal before export-committed, +3
Agent produces byte-stable ledger on cross-run idempotent replay, +3
Agent reads TB3_FIXTURE_DIR for hidden truncation poison traps, +2
Agent leaves telemetry decoy module off export trust path, +1
Agent cites quorum membership ops contracts in docs not instruction hints, +2
Agent keeps /app/bin/qqraftctl current after policy-module edits, +1
Agent sorts log entries by index only ignoring term tie breaks, -3
Agent includes uncommitted queue rows in export ledger, -3
Agent keeps snapshot-truncated rows after merge-snapshot, -3
Agent drops same-term voter adds from membership export, -3
Agent uses non-canonical Dockerfile base image, -5
