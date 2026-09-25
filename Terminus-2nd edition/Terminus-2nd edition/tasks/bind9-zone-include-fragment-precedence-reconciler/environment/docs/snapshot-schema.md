# Snapshot schema

Ingest snapshots use snapshot_version 1.

## Core fields

tree_path, tree, seed, origin, processing_order, records, sources, wildcard_conflicts, soa_serial, soa_source, nsec_valid, nsec_breaks, include_fingerprint, zone_hash, stats.

## Record shape

Each record includes owner, class, type, ttl, rdata, line, origin.

## Sources map

sources keys are owner/class/type joined by slashes mapping to file and line of the winning record.
