# Workshop mount-plan ops control plane

workshop-plan plan runs four host-local ops stages on each offline ops pass:

1. Parse — /app/lib/vdf_parse.sh reads manifest.vdf into a temporary TSV stream.
2. Stage — /app/lib/staging.sh admits the stream to /app/state/parsed-manifest.tsv and writes /app/state/staging-meta.json (see staging-schema.md).
3. Resolve — /app/lib/deps.sh reads staged TSV, enforces semver and missing-dep barriers, and writes a graph TSV. /app/lib/topo.sh computes mount_order and cycles per plan-contract.md.
4. Export — /app/lib/export_plan.sh validates the staging digest gate, updates /app/state/run-seq.json, and publishes sealed plan JSON per plan-output-schema.md.

/app/decoy/legacy_mount.sh is a retired helper and is not sourced by workshop-plan.

## Run sequence

/app/state/run-seq.json stores:

```json
{"seq": 1, "input_fingerprint": "<sha256 hex>"}
```

input_fingerprint is SHA-256 over the manifest file bytes, a newline, and canonical JSON for the config object (sorted keys, compact separators).

When the fingerprint matches the stored value on a successful exit 0, seq stays unchanged. When the fingerprint changes, seq increments by one. The plan footer.run_seq field mirrors seq after export.

Failed runs (exit 1 or 2) never create or update run-seq.json and never increment seq. With no prior run-seq.json, footer.run_seq is still 1. With prior state, footer.run_seq retains the existing seq and the on-disk file is left untouched.

Each run replaces staging files, graph temps, and the output plan. run-seq.json persists until reset-state.sh (and only advances on successful exit 0).
