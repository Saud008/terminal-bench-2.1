# Export report schema

Path: /app/output/radius-acct-flush-report.json

Fields:

- proxy_name, home_server: copied from snapshot
- sessions: same array as snapshot sessions
- sessions_completed: count of sessions with status stopped only
- interim_flushed: equals stats.interim_flushed from snapshot (proxy batches), not interim timestamps on stopped rows
- flush_batches: stats.flush_batches
- stats: full stats object from snapshot
