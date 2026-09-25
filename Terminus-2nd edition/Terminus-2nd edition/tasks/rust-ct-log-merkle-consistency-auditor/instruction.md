Task identity f3c91e7a2b — CT log witness auditor.

# Witness auditor for Certificate Transparency logs

Build the release CLI documented in /app/docs/stage_seal_pipeline.md so compliance officers can validate CT log checkpoints before archiving witness evidence. The tool under /app ingests a JSON audit index, loads per-log signed tree head bundles, tallies independent cosigner checkpoints, and emits a sealed JSON archive for downstream review.

Pytest rebuilds the Rust binary on every run. Complete the staged ingest and seal workflow so emitted JSON matches the contracts in /app/docs without hard-coded literals in tests.

## Operational workflow

Rebuild with /app/environment/scripts/rebuild_ctwrelease.sh.

Stage bundles from /app/environment/fixtures/audit_index.json and /app/environment/fixtures/witness_ledger.json per /app/docs/stage_seal_pipeline.md. Persist checkpoint rows at /app/state/checkpoint_rows.json.

Seal those rows per the same pipeline doc. Publish the compliance archive at /app/output/witness_evidence_archive.json.

## Behavioral contracts (read the docs)

Witness checkpoint JSON layout is in /app/docs/ct_checkpoint_manifest.md.

RFC 6962 tree inclusion and append-only growth proofs are in /app/docs/rfc6962_tree_paths.md.

Cosigner agreement rules are in /app/docs/witness_attestation_quorum.md.

Sealed archive schema and bundle_digest rules are in /app/docs/sealed_evidence_archive.md.

CLI flags and TB3_AUDIT_INDEX / TB3_WITNESS_LEDGER overrides are in /app/docs/stage_seal_pipeline.md. Hidden verifier probes may load fixtures from /opt/verifier-fixtures/ct_hidden when TB3 variables aim there.

Independent witness math for pytest is at /app/environment/verifier_contracts/ct_audit_refmath.py. Tests call the release CLI through subprocess helpers in conftest. Static JSON literals will not pass.
