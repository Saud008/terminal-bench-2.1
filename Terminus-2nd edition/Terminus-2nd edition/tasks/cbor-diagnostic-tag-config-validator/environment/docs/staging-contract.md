# Staging contract

Path: /app/state/staging.cbor

Written only after ingest validation succeeds.

## Canonical map key order (signing order)

The staged CBOR map must use this insertion order:

1. version
2. bundle_id
3. diagnostic_tags
4. envelope

Do not sort keys lexicographically. The attestation digest and HMAC are computed over these exact bytes.

## diagnostic_tags

Same array order and per-item key order as the source bundle (label then tag).

## envelope

Re-encoded tag 24 wrapper around the policy map. The length prefix must match the inner CBOR length rules in /app/docs/cbor-bundle-format.md.

## Validation before write

Staging validation (non-empty bundle_id, policy, nonce) must complete before /app/state/staging.cbor is created. Failed ingests must not leave a staging file behind.
