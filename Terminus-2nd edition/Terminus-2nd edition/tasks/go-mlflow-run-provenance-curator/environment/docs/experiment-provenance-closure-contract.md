# Experiment provenance closure contract

Independent reference math for this numerical simulation task.

## Lineage closure

Given a focus training-run id and the staged run catalog, compute root-first ancestry closure by walking `parent_run_id` links. The focus run is last; the experiment root is first. Siblings and child branches are excluded.

## Metric epoch monotonicity

Sort metrics by epoch ascending, then step ascending, then key ascending. `epoch_monotonic_ok` is true only when every metric in a later epoch has step greater than or equal to the maximum step observed in the previous epoch group after that ordering.

## Model artifact digest closure

Normalize each artifact `rel_path` by removing a leading `./` prefix. Digest is SHA-256 over `rel_path + "\n" + content` UTF-8 bytes, lowercase hex. Emit digests sorted lexicographically by normalized path.

## Feature dataset binding

Compare each focus-run dataset pin `version_hash` to the manifest hash for that dataset name. Apply active `TB3_MANIFEST_SALT` suffix to manifest hashes before comparison when the environment variable is set. `binding_ok` is true only when every pin matches and at least one pin exists.

## Audit digest closure

`audit_digest` is SHA-256 over compact JSON with keys in this fixed order: `artifact_count`, `binding_ok`, `epoch_monotonic_ok`, `lineage_depth`, `lineage_chain`, `version_hashes`. Booleans are lowercase JSON literals. `lineage_chain` is a compact JSON array of scoped run-id strings root-first. `version_hashes` is a compact JSON array of manifest version_hash strings after salt, sorted lexicographically.

## Persistence handoff

Publish certificate must read both the staged snapshot and the active curated row for the seed. Export from staging alone without the SQLite handoff is incorrect.
