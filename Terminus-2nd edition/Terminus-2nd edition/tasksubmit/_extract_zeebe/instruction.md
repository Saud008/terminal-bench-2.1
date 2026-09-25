Machine-learning activation-barrier feature ranking lab

Machine-learning operators need zeebe-bpmn-replay for offline activation-barrier feature ranking and sealed activation-atlas eval on scenario packs under `/app`. The lab loads JSON scenarios from `/app/fixtures/scenarios/`, builds readiness features from incident-marker timing, boundary-window traps, process-clock deadlines, overlay-merge shelves, and idempotent-replay dedup gates, writes a normalized staging snapshot at `/app/state/incident-snapshot.json`, and seals an eval atlas report at the caller-provided `--output` path (default `/app/output/job-activation-export.json` for merged packs). This is a machine-learning activation-feature ranking and atlas-eval workflow. It is not a software-engineering service repair, Go module rebuild, debugging task, games playtest lipstick, system-administration ops desk, BPMN broker operations, or data-processing pipeline.

Install / rebuild the CLI at `/usr/local/bin/zeebe-bpmn-replay` from `/app`. Primary command:

```text
zeebe-bpmn-replay export --scenario PATH --output PATH
```

Reported fields, feature definitions, barrier timing, boundary traps, deadline derivation, overlay merge, replay dedup, staging schema, sealed atlas schema, and refusal exit codes must match the contracts under `/app/docs/` for every bundled and hidden scenario:

- `/app/docs/incident-barrier.md` — incident-linked jobs stay off the activation sequence until `marker_persisted_at_ms` is logged; activation time is `max(intent_at_ms, marker_persisted_at_ms)` with barrier `incident_marker_persisted` when gated and `none` otherwise
- `/app/docs/boundary-ordering.md` — boundary events attached to an element may fire only after every job on that element has left its activating window
- `/app/docs/job-deadline-clock.md` — `deadline_ms` equals `process_clock_ms + job_timeout_ms` with `deadline_clock_source` `process`
- `/app/docs/variable-merge.md` — incident overlays merge into working variables without clobbering output-mapping source keys; `resolved_outputs` come from the merged working map
- `/app/docs/replay-dedup.md` — idempotent replay batches skip duplicate `batch_id:job_key` activations and count them in `duplicate_activations_skipped`
- `/app/docs/staging-snapshot.md` — staging snapshot fields written during ingest before sealed atlas emit
- `/app/docs/export-schema.md` — sealed activation atlas field order
- `/app/docs/cli-errors.md` — refusal exit codes
- `/app/docs/fixture-catalog.md` — bundled scenario inventory

`export` must materialize `/app/state/incident-snapshot.json` during ingest, then emit the sealed atlas only from that staged snapshot. Hidden verifier scenarios may appear under `/opt/verifier-fixtures/zeebe-bpmn`. `/app/docs/`, `/app/fixtures/`, and `/app/config/` are read-only inputs that define the ranking contracts and fixture inventory. The `internal/router` decoy package is not on the export ranking hot path and must not be edited for a correct atlas. Offline only.
