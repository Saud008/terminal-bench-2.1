# Staging resolution schema

Analyze materializes the resolution snapshot at `/app/state/whres-snapshot.json`.

The snapshot JSON object stores these top-level keys: `run_id`, `scenario`, `target_python`, `target_platform`, `target_arch`, `index_fingerprint`, `packages`, `queries`, and `snapshot_digest`.

## snapshot_digest

`snapshot_digest` is the lowercase hex SHA-256 of one compact JSON object. Build that object with exactly these keys:

- `run_id` (string)
- `index_fingerprint` (string)
- `target_python` (string)
- `target_platform` (string)
- `target_arch` (string)
- `packages` (array)

Each `packages` array entry must be an object with exactly two string keys: `package` and `version`. Include every package row from the snapshot `packages` list in the same order as the snapshot, using only those two fields (omit yanked, tags, hashes, and other index columns from the digest input).

Serialize the digest input object as compact JSON with lexicographically sorted object keys and no ASCII whitespace between tokens (equivalent to sorted keys with separators comma and colon, no spaces). Hash the UTF-8 bytes of that serialization with SHA-256 and write the hex digest into `snapshot_digest`.
