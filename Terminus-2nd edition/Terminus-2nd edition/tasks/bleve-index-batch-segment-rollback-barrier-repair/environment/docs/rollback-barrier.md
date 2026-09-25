# Rollback barrier — index-ops admission gates

Failed ingest operations must respect rollback barriers on this host-local system-administration control plane.

Rollback guarantees:
- No stale segment pointer remains in root mapping after a failed batch
- No orphan segment file remains on disk after rollback
- Persistent document counter must not advance for rejected records
- Export must remain usable immediately after a failed ingest

Rollback semantics apply to every batch file passed to ingest, including checksum-invalid lines mixed with valid records.

## Merge scheduling barriers

Merge work is represented by merge-plan.json under each index root (default prefix /app/state/indexes, or /app/state/tb3-indexes when TB3_INDEX_PREFIX is set).

Merge scheduling must respect two barriers:

1. Open-batch barrier: do not write merge-plan.json while the ingest batch barrier is open. The barrier is the on-disk `open-batch.flag` under the index root. Scheduling runs only after that flag is cleared for the current batch. Callers must clear the flag before invoking merge scheduling, and the scheduler must also observe the on-disk flag (not only a caller-supplied boolean).
2. Segment-count threshold: do not write merge-plan.json when the root map lists fewer than two committed segments. A single successful ingest that leaves one segment must not produce a merge plan.

When both barriers are satisfied, merge-plan.json must be written for that index with this JSON object shape:
- `scheduled`: boolean `true`
- `open_batch`: boolean `false`
- `segment_count`: integer equal to the number of committed segment file names in the root map
- `segments`: array of segment file names, identical to the root map `segments` list at schedule time
