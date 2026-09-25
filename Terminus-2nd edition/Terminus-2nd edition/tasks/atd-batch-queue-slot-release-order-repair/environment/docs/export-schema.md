# export schema

Replay export JSON is one object. The verifier compares the full document with exact JSON equality against the reference replay. Every nested object must contain only the keys listed for that shape. Do not add extra fields even when a hook receives additional arguments.

## top-level fields

export_version is integer 1.

scenario is the scenario directory name.

seed is the string passed to replay --seed (recorded only; scheduling math must not depend on seed).

clock_epoch is the replay instant in seconds.

timezone is the scenario system_timezone string.

jobs_run is an array of job keys (batch_id:job_id) in scenario iteration order for jobs that entered the run path (including jobs left pending in spool).

jobs_skipped is an array of skip records (see jobs_skipped entry).

timeline is an array of timeline events (see timeline entry).

registry_final maps job key strings to registry records still on disk after replay (see registry_final record).

mail_log is an array of failure mail records (see mail_log entry).

atq_lines is an array of pending spool rows after replay (see atq_lines entry).

seq_final is the integer read from /app/var/spool/at/.SEQ after replay.

batch_slots_held is an array of letter strings for batch slot markers still present after replay.

## jobs_skipped entry

Each entry contains exactly:

job: job key string (batch_id:job_id).

reason: not_due when clock_epoch is before the job atq_epoch, or no_slot when letter allocation fails.

No other keys.

## timeline entry

Each entry contains exactly:

seq: integer event counter starting at 1 and increasing by 1 per emitted event.

event: one of registry_read, slot_allocate, spool_write, slot_release, job_complete, registry_delete, mail_sent, seq_bump, atq_refresh.

job: job key string for job-scoped events, or the literal string system for atq_refresh.

epoch: integer clock epoch attached to this event.

No other keys.

## registry_final record

Each value in registry_final contains exactly:

completed_at: integer epoch when the record was written.

dispatch_meta: object (see dispatch_meta).

flushed: boolean true.

No other keys. Job keys with no remaining file on disk are omitted from registry_final.

## dispatch_meta object

Each dispatch_meta contains exactly:

interpreter: shell name parsed from the job script shebang (for example sh).

effective_umask: four-digit zero-padded octal umask string (for example 0022).

No other keys.

## mail_log entry

Each failure mail record contains exactly:

job: job key string.

exit_code: integer non-zero exit code from the scenario job definition.

No other keys. notify_failure receives an epoch argument for timeline ordering, but mail_log entries must not include epoch or any other field.

## atq_lines entry

Each pending spool row contains exactly:

name: spool file name (starting letter plus ten-digit sequence).

atq_epoch: integer ATQ_EPOCH parsed from the spool header line.

batch: string BATCH from the spool header line.

job: string JOB from the spool header line.

No other keys. Sort ascending by atq_epoch, then by name. File modification time must not influence ordering (see /app/docs/atq-display.md).
