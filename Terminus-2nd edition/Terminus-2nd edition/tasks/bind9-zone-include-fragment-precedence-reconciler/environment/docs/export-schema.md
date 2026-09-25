# Export compile schema

compile and export emit JSON with compile_version 1.

## Required fields

tree, seed, origin, processing_order, records, soa_serial, wildcard_conflicts, nsec_valid, include_fingerprint, zone_hash, compile_digest, stats.

## Digest

compile_digest must use canonical_snapshot_digest of the source snapshot, not legacy_effective_digest.

## Pipeline

compile runs ingest then export. export reads an existing snapshot only and must not re-parse zone files from disk.
