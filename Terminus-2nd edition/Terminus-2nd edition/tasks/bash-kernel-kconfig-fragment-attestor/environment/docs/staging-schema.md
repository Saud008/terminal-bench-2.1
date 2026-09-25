# Stage snapshot schema

kcfg-stage.json fields:

run_id, bundle, fragment_order, raw_merged, after_deps, policy_violations, deps, policy, stage_digest.

stage_digest is sha256 of JSON object with run_id, bundle, fragment_order array, and symbol_count from after_deps.

compile-stage writes kcfg-stage.json to /app/state/kcfg-stage.json before emit-manifest reads this snapshot only.

Cross-run tests call /app/scripts/reset-state.sh before rebuilding the same run id.

TB3_BUNDLE_ROOT overrides the bundle root for verifier overlay bundles under /opt/verifier-fixtures/kcfg/bundles/.
