# Logical types and parsing canonical fingerprint

## Decimal logical type

For bytes fields with logicalType decimal, reader precision must be greater than or equal to writer precision and reader scale must equal writer scale.

## Timestamp millis

Both writer and reader must agree on logicalType timestamp-millis for the same field name when either side declares it.

## Parsing canonical fingerprint

Compute a 16-hex-character canonical_fp from the parsing canonical form:

1. Remove doc, default, and aliases keys recursively.
2. For record types, sort fields array by field name ascending before hashing.
3. Sort object keys lexicographically at every object level.
4. Serialize to compact JSON and apply SHA-256 via hashlib.sha256 in reference checks; take the first 16 hex chars.

Fingerprints must be stable across equivalent schemas that differ only in field declaration order.
