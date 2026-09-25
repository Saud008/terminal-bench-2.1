# Ledger export schema

export ledger writes /app/output/release-witness-ledger.json using staging at /app/state/tw-approval-stage.json and quorum verdict at /app/state/quorum-verdict.json only.

Top-level fields:

- release_id from staging policy
- artifact_digest from staging artifact digest
- epoch, quorum_met, valid_witness_count, threshold from verify-result
- ingest_seq from staging
- witnesses array sorted by witness_id ascending

Each witnesses row contains witness_id, signer_keyid, epoch, prior_witness_id, counts_toward_quorum from verify outcomes.

ledger_digest is lowercase hex sha256 over canonical JSON with keys artifact_digest and witnesses where witnesses is a JSON array of objects sorted by witness_id with fields witness_id, signer_keyid, epoch, prior_witness_id, counts_toward_quorum.

export must not read witness JSON from the ingest bundle directory when building ledger_digest or witness rows.
