# Feature run snapshot schema

Hydrate writes a JSON feature-run snapshot to /app/state/provenance-staging.json for the active training run under review.

The snapshot records the active seed and scenario, a monotonically increasing ingest_seq, the scoped focus_run_id for the model run under inspection, the feature dataset_manifests map keyed by dataset name, and the seed-scoped experiment run catalog used by closure bind and certificate publish.

A scoped run id uses the raw run id followed by `-<8 lowercase hex>`, where the suffix is the 32-bit FNV-1a hash of `seed + ":" + raw_run_id`. `focus_run_id`, every staged `run_id`, and every staged `parent_run_id` use that same seed-scoped format.

Each staged run carries its scoped run_id, parent_run_id, params, metrics, artifacts, and dataset_pins. Artifact entries retain rel_path and UTF-8 content exactly as stored in the scenario catalog so later digest closure checks can operate on staged data instead of reparsing fixtures.
