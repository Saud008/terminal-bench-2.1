Implement the four-stage workshop-plan pipeline under /app/bin/workshop-plan so Steam-style workshop manifest directories produce compliant staging artifacts, dependency resolution, topological mount ordering, and /app/output/plan.json per /app/docs/plan-contract.md, /app/docs/staging-schema.md, /app/docs/pipeline-overview.md, /app/docs/plan-output-schema.md, and /app/docs/vdf-manifest-format.md.

Stage 1 (/app/ingest/manifest_ingest.sh) parses manifest.vdf via /app/lib/vdf_parse.sh and commits staging through /app/lib/staging.sh to /app/state/parsed-manifest.tsv and /app/state/staging-meta.json (see staging-schema). Stage 2 (/app/lib/deps.sh) reads staged TSV only, validates semver and missing dependencies, and builds the required-edge graph. Stage 2 continues in /app/lib/topo.sh with layer-by-layer Kahn ordering and contract cycle paths. Stage 3 (/app/lib/export_plan.sh) validates the staging digest, maintains /app/state/run-seq.json across runs, and writes the final plan JSON.

Cross-stage invariants require export to reject stale staging digests and mirror run_seq in the plan footer after successful exit 0. Re-running the same manifest directory and config must produce identical plan JSON and an unchanged run_seq when the input fingerprint is unchanged.

/app/decoy/legacy_mount.sh and /app/wrap/decoy_topo.sh are retired helpers and are not invoked by workshop-plan.

Exit 0 on success. Exit 1 when required dependencies are missing or semver constraints fail (with errors recorded in output). Exit 2 when a dependency cycle is detected and the config disallows emitting a sort.

Use /app/scripts/reset-state.sh before local runs. Example:

/app/scripts/reset-state.sh
/app/bin/workshop-plan plan --manifest-dir /app/fixtures/workshop/001-linear --config /app/config/plan.json --output /app/output/plan.json

Do not edit /app/docs/, /app/fixtures/, /app/config/plan.json, or files under /tests/.
