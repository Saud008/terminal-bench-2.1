# Run directory layout

Each scenario run directory under the fixture root contains:

- run.meta.json — run_id, session_id, resumed boolean
- trace/*.json — one task record per file (see task-record-schema.md)
- inputs/ — sample files referenced by input_globs
- work/<task_id_sanitized>/.nf_cached.json — cache provenance marker when cached

## Container digest normalization

Recorded container_digest values may include a sha256: prefix. Before staging or comparison, normalize by trimming whitespace, removing a case-insensitive sha256: prefix, and lowercasing the remaining hex digest.

## Glob expansion

Input globs are relative to the run directory. Expansion must collect matching paths, convert to forward-slash relative paths, sort lexicographically, then hash each path separated by NUL bytes into expansion_hash.
