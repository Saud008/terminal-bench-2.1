# Trust ledger workflow

sshap ingest reads principals, CA material, and KRL revocations into /app/state/trust_ledger.json with a stable ledger_fingerprint. Rows sort by scope_id, deny flag, rank, and principal text.

sshap attest reads the ledger plus Match snippets and probe definitions to write /app/output/principals_attestation_bundle.json. When TB3_MATCH_DIR and TB3_PROBES_FILE are set, attest uses those paths instead of bundled fixtures.

The decoy helper under /app/lib/decoy is not authoritative for ingest or attest ordering.

Binding reason codes are revoked, ca_scope, principal_match, wildcard_denied, and no_match. Session bindings sort by probe_id. bundle_seal seals ordered binding_seal lines.
