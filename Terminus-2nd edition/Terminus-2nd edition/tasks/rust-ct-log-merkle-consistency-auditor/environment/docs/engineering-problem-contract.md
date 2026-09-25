# Engineering problem contract — rust-ct-log-merkle-consistency-auditor

Certificate Transparency witness auditors reconcile signed tree heads with third-party cosigner checkpoints before sealed compliance export. Failure modes span RFC 6962 leaf hashing, append-only growth witnesses, cosigner quorum tallies, monotonic timestamps, lowercase root normalization, lexicographic row ordering, and bundle digest binding over exported audit rows.

Verifier contracts require subprocess CLI staging at /app/state/checkpoint_rows.json and sealing at /app/output/witness_evidence_archive.json with independent witness_refmath cross-checks.
