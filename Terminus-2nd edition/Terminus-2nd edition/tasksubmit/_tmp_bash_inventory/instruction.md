Machine-learning operators need hostsatlas for offline host-feature precedence ranking and sealed atlas eval on inventory scenario trees under /app. The lab loads tree manifests, builds effective host-feature maps from ordered group-layer and host-layer stacks, scores marker-token and ignore-pattern traps, writes a normalized staging snapshot under /app/state, and seals an eval atlas report under /app/output. This is a machine-learning host-feature ranking and atlas-eval workflow.

Install the CLI at /usr/local/bin/hostsatlas (also /app/scripts/hostsatlas). Reported fields, layer-stack order, trap scoring, digests, and sealed schemas must match the contracts under /app/docs/ and class weights in /app/config/severity-weights.json.

Primary commands:

  hostsatlas scan --tree PATH
  hostsatlas emit --tree NAME --output PATH

scan --tree PATH loads one inventory scenario tree manifest, writes the staging snapshot at /app/state/host-rows.ndjson, /app/state/atlas-rows.ndjson, and /app/state/scan-manifest.json, and binds staging_digest over host-rows then atlas-rows bytes. Scan must not write sealed atlas JSON under /app/output. That digest must stay stable when the tree fingerprint is unchanged. Cross-run eval counters track /app/state/run-seq.json and tree fingerprints so re-scanning an unchanged tree keeps run_seq stable.

emit --tree NAME --output PATH seals atlas eval JSON at the caller-provided --output path only from those on-disk staged witnesses. When --output is omitted, write /app/output/hosts-atlas-report.json as the sealed atlas. Emit must never reopen inventory hosts.ini, group_vars, or host_vars paths from the tree manifest after scan completes. When staged artifacts are missing or the active tree id does not match, emit leaves --output unpublished and exits 3.

Feature-layer merge order, parent-to-child stack ranking, ignore-pattern traps, marker-token scoring, staging fields, run_seq stability, and sealed schemas follow /app/docs/. Bundled scenario trees live under /app/fixtures/trees/. Hidden verifier trees live under /opt/verifier-fixtures/tb3-trees/. Decoy helpers under /app/decoy/ and /app/wrap/ stay outside the scan and emit eval hot path. Do not modify /app/docs/, /app/fixtures/, /app/config/, or /tests/. Offline only.

Example eval passes:

/app/scripts/reset-state.sh
/app/scripts/hostsatlas scan --tree /app/fixtures/trees/clean-tree/tree.json
/app/scripts/hostsatlas emit --tree clean-tree --output /app/output/hosts-atlas-report.json
/app/scripts/hostsatlas scan --tree /app/fixtures/trees/precedence-trap/tree.json
/app/scripts/hostsatlas emit --tree precedence-trap --output /app/output/hosts-atlas-report.json

Exit 0 on success. Exit 2 when scan cannot read the tree manifest. Exit 3 when emit runs before a matching scan snapshot exists.
