# Digest contract

canonical_snapshot_digest hashes JSON with keys origin, processing_order, records, soa_serial, include_fingerprint using sorted keys and compact separators.

The include_fingerprint value in that payload must be the exact value defined in cache-invalidation.md. Changes to the scanned .zone file set, relative-path ordering, per-file SHA-256 truncation, or the literal | join format therefore change both snapshot zone_hash and export compile_digest.

legacy_effective_digest hashes only sorted owner/type key names and is deprecated for staging or export digests.
