# Signing and attestation export

Export writes JSON to the path given by --report (default /app/output/attestation.json).

## Fields

- bundle_id — text from the latest ingest
- staged_digest — lowercase hex SHA-256 of canonical staging bytes per /app/docs/staging-contract.md (not the on-disk staging file when it differs, not the ingest bundle)
- signature — lowercase hex HMAC-SHA256 of the same canonical staging bytes keyed by /app/config/signing.key (raw file bytes as key material)
- audit_row_count — count of ingest audit rows for bundle_id
- diagnostic_tag_summary — array of {label, tag} objects in ingest order

## HMAC message range

The HMAC input is the canonical staging byte sequence defined in /app/docs/staging-contract.md (version-first map key order and tag-24 envelope encoding per /app/docs/cbor-bundle-format.md).

The optional --ingest-source flag is for debugging only; attestation must still use canonical staging bytes for signature verification.

## Key material

/app/config/signing.key — UTF-8 string used directly as the HMAC key (not hex-decoded).
