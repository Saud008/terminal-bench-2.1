# Eval summary certificate fields

Publish summary writes one JSON eval closure certificate for the requested seed and scenario. The certificate combines the latest curated database row with the feature-run snapshot that produced it, so each top-level field must stay stable across repeated publishes of the same curated state.

## Top-level fields

- `seed`: active seed string
- `scenario`: active scenario name
- `focus_run_id`: scoped focus run id from staging using the seed-scoped `<raw-run-id>-<8 lowercase hex>` FNV-1a format defined in `feature-run-snapshot-schema.md`
- `run_id`: integer curation id from `curation_runs`
- `lineage_chain`: root-first array of scoped run ids in that same seed-scoped format
- `artifact_digests`: sorted array of `{ rel_path, digest }` objects
- `metric_epochs`: ordered metric objects from the focus run
- `dataset_bindings`: binding rows described in `feature-dataset-binding.md`- `summary`: compact status object with `binding_ok`, `epoch_monotonic_ok`, `lineage_depth`, and `artifact_count`
- `audit_digest`: SHA-256 hex digest over the canonical summary body described below

## Ordering and validation rules

`metric_epochs` is sorted by epoch ascending, then step ascending, then key ascending. `epoch_monotonic_ok` is true only when every metric that belongs to a later epoch has a step greater than or equal to the maximum step observed in the previous epoch group after that ordering is applied.

`artifact_digests` is sorted lexicographically by normalized `rel_path`. `dataset_bindings` must report the focus run pins after manifest matching, including any active `TB3_MANIFEST_SALT` adjustment described in the dataset binding contract.

The bundled curator flow writes report filenames under `/app/output/` that end with `-provenance.json` when the standard helper path convention is used.

## Canonical audit digest

`audit_digest` is SHA-256 over a compact JSON object. The object keys must appear in this fixed sequence (not alphabetically sorted object keys): `artifact_count`, `binding_ok`, `epoch_monotonic_ok`, `lineage_depth`, `lineage_chain`, and `version_hashes`. Booleans stay lowercase JSON literals (`true` or `false`). `lineage_chain` is encoded as a compact JSON array of scoped run-id strings in root-first order. `version_hashes` is a compact JSON array of manifest `version_hash` strings after any active `TB3_MANIFEST_SALT` suffix is applied, with the array sorted lexicographically by string value. Hash the UTF-8 bytes of that compact JSON with no extra whitespace.
