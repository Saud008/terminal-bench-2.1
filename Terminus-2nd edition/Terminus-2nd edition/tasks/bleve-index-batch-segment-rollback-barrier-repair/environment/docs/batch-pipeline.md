# Batch pipeline — host-local index-ops control plane

This task is a **system-administration** host-local blevectl index-ops control plane. Operators admit JSONL batches into a named index, enforce open-batch rollback barriers and merge scheduling gates, and publish sealed collator-ordered export manifests from committed state only. The working baseline under /app must keep admission gates, rollback barriers, and sealed export aligned; it is not a generic service repair exercise.

The ingest command consumes one JSONL batch at a time and updates a named index.

Each record line must include:
- id
- key
- payload
- checksum

Batch ingestion has three logical stages:
1. Parse and stage the batch
2. Verify checksum integrity (FNV-1 per zap-segment-format.md) before writing index-visible segment files or advancing persistent document counters
3. Commit index-visible pointers, clear the on-disk open-batch barrier (`open-batch.flag`), then conditionally schedule merge work

Stage three must clear the open-batch barrier before any merge scheduling attempt. Merge scheduling is conditional: see rollback-barrier.md for the on-disk barrier check, the segment-count threshold, and the required merge-plan.json fields (including `segments`). A lone committed segment after one ingest must not emit merge-plan.json.

If any record in the batch fails checksum validation, the command must return non-zero and leave index-visible state unchanged (no new root-map pointers, no orphan segment files, no counter advance).
