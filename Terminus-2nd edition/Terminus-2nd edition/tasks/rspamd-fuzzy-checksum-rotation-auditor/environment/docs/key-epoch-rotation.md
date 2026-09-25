# Key epoch rotation

The key manifest JSON fields:

- schema: integer, always 1
- key_epoch: positive integer rotation epoch
- checksum_algo_id: positive integer algorithm selector rotated with the epoch
- epoch_salt: string salt mixed into snapshot digests

On every non-dry-run rotate invocation, before inserting new shingles, update every row in fuzzy_hashes so both key_epoch and checksum_algo_id match the manifest. Recompute stored hash values for existing rows using the new epoch and algorithm id with the same shingle text preserved in the shingles column.

If console verification fails after sqlite mutation, write /app/state/rotation-rollback.json with schema 1, key_epoch, checksum_algo_id, and reason set to console_mismatch, then exit non-zero. Do not leave a half-updated index without this rollback marker.

When RF_EPOCH_SALT_SUFFIX is set, append its value to epoch_salt only for shingle snapshot digest computation (not for per-shingle hash strings).

Dry-run must skip sqlite mutation, rollback files, and rotation-run.json.
