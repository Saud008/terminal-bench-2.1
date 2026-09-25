# Denial chain validation contract

The nsecval validate subcommand walks stub-zone captures and decides whether each query is consistent with published NSEC and NSEC3 denial proofs.

## Capture input

Captures are JSON files with zone, soa_serial, nsec3_params, records, and queries. Each record uses owner, rtype, next, type_bitmap for NSEC, or hash_owner, next_hashed, iterations, salt_hex for NSEC3. Queries list qname, qtype, expect (valid or invalid), and optional soa_serial.

## Chain validation

Before query walking, validate checks that plain NSEC records form a single canonical-order chain around the zone apex. Owner ordering and next linkage follow /app/docs/nsec-ordering.md (folded full-string lexicographic order, not wire label order). The next field of each sorted NSEC must equal the owner of the successor record, wrapping at the zone boundary.

## Query walking

For each query, if soa_serial is present on the query object, the stub cache must observe that serial before evaluation. When a newly observed serial is strictly less than the highest serial already seen, the denial cache must be cleared entirely.

Denial evaluation order: closest covering NSEC name error proof first, then NSEC3 covering proof, then wildcard expansion last. A query is valid when expect is valid and the proof path matches; invalid when expect is invalid and a proper denial proof exists.

## Outputs

validate writes validation-report.json with zone, soa_serial, chain_valid, queries (status and proof kind), cache_hits, and snapshot_sha256 matching the ingest snapshot bytes.

ingest writes chain-snapshot.json under /app/state with zone, soa_serial, record_count, and records array.
