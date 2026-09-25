# Snapshot validation before publish

Publish must call lt_validate_snapshot immediately after confirming /app/state/lt-scan-snapshot.json exists and before building manifest rows.

## Required checks

1. Every direct_deps entry in the snapshot uses the lib-prefixed id form (libcore, not core).
2. broken_edges is sorted lexicographically by from then to (UTF-8 / LC_ALL=C).
3. snapshot_fingerprint matches the digest computed during scan staging.

## snapshot_fingerprint algorithm

After cycle breaking, canonicalize the snapshot body:

1. Sort libraries by id ascending.
2. For each library, emit one line: id:sorted_comma_joined_direct_deps (empty string when none).
3. For each broken edge (sorted by from then to), emit one line: from/to.
4. Join lines with newline (no trailing newline). SHA-256 hex digest of UTF-8 bytes is snapshot_fingerprint.

Scan staging must write this field. Publish rejects snapshots with a missing or mismatched fingerprint.

## Failure mode

When validation fails, publish must exit non-zero and must not write the manifest file.
