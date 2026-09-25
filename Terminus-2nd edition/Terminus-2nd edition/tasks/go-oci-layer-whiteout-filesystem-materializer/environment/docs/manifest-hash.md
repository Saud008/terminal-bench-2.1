# Manifest hash

The exported manifest at /app/output/filesystem-atlas.json includes `manifest_hash`.

Compute `manifest_hash` only from the materialized export entries, not from staging members or raw tar metadata.

Steps:

1. Sort export entries by `path` ascending using byte-wise string order.
2. For each entry build canonical JSON with keys sorted lexicographically: `gid`, `mode`, `path`, `type`, `uid`.
3. `mode` is a four-digit octal string such as `0644`.
4. Join canonical JSON lines with a single newline character.
5. `manifest_hash` is the lowercase hex SHA-256 digest of the joined UTF-8 bytes.
6. An empty entry list hashes the empty byte slice.

The `entries` array in the output file uses the same sort order as the hash input.
