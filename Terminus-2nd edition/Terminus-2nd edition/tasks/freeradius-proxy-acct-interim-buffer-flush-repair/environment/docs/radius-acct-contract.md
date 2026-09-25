# RADIUS proxy accounting contract

Local simulator only — not a live FreeRADIUS deployment.

## Two-stage pipeline

ingest replays JSONL accounting captures, writes /app/state/acct-flush-snapshot.json and /app/state/acct-ledger.db.

export reads the snapshot JSON only and writes /app/output/radius-acct-flush-report.json. export must not read JSONL logs or rebuild from fixtures.

## Session lineage

A session is keyed by nas_id, Acct-Session-Id, and Acct-Unique-Session-Id together. When a Start arrives with the same Acct-Session-Id but a different Acct-Unique-Session-Id than the active lineage on that NAS, treat it as a NAS reboot lineage: increment reboot_lineages and start a new session row without merging octets into the prior unique id.

Interim-Update and Stop must target the session matching the packet unique id when present; never attach to an older unique id with the same Acct-Session-Id.

## Interim buffer flush

Interim-Update packets enqueue into the proxy flush buffer. When now_ts minus last_flush_ts for the session is at least the effective interim interval, eligible entries flush in a batch. increment flush_batches once per batch and interim_flushed by the number of entries flushed.

Stop marks the session stopped, increments sessions_stopped, and forces a final flush batch for pending interim entries on that session.

## SQLite persistence

After writing session_ledger and flush_ledger rows, run PRAGMA wal_checkpoint(FULL) once per ingest run on both success and error rollback paths. increment wal_checkpoints once when checkpoint succeeds.

## Export counts

sessions_completed counts sessions with status stopped only. interim_flushed in the export document equals stats.interim_flushed from the snapshot, not a recount of interim timestamps on stopped sessions.
