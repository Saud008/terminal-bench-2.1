IPsec fleet operators need a host-local strongSwan VICI security-association rekey attestation control plane. Offline VICI traces must be judged against CHILD_SA delete-before-rekey ordering, traffic-selector widening trust gates, IKE unique-id slot lifecycle, and monotonic event-sequence integrity so that only policy-faithful active SPI state is sealed into the exported security report.

Operate the vicireplay CLI under /app/cmd/vicireplay so that every conforming JSONL trace under /app/fixtures/traces/ (and any other valid trace under the documented format) persists a staged snapshot at /app/state/rekey-snapshot.json matching the replay timeline, then exports /app/output/rekey-report.json whose verdicts, active_spi_out, rekey_violation_count, and per-event flags match those events. Export must read the staged snapshot manifest only and must not re-parse trace files or re-run replay logic during export.

Example:

vicireplay replay --trace /app/fixtures/traces/001-fresh-child.jsonl --output /app/output/rekey-report.json

## Reference

Trace layout is in /app/docs/vici-trace-format.md. CHILD_SA delete-before-rekey ordering is in /app/docs/rekey-delete-order.md. Traffic selector widening on rekey is in /app/docs/selector-widen-policy.md. IKE_SA unique-id slot lifecycle is in /app/docs/ike-uid-lifecycle.md. Event log_seq monotonicity across rekey is in /app/docs/event-sequence-policy.md. Staging fields are in /app/docs/staging-snapshot.md and exported active SPI rules in /app/docs/export-schema.md. The ingest-to-export pipeline is summarized in /app/docs/ingest-export-pipeline.md.

Initiator id offsets follow VERIFIER_INITIATOR_OFFSET when set, otherwise default. After Go changes under /app/internal/, rebuild vicireplay before grading. Do not edit /app/docs/, /app/fixtures/, or /app/config/, and do not replace the tool with a hardcoded report writer.
