Replay report JSON written to --output:

workflow_id, visibility_deadline_ms, last_progress_seq, sticky_partition, history_cursor_seq, history_events_applied, duplicate_events_skipped, decision_task_lost, timed_out, query_results, lost_decision_reason, last_heartbeat_ms.

Runtime snapshot at --state mirrors visibility, progress, sticky partition, cursor, duplicate count, decision_task_lost, timed_out.

Subcommands: replay (--scenario, --output, --state), dump-report (--output).
