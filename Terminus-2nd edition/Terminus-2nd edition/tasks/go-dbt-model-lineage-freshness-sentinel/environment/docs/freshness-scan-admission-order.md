# Freshness scan admission order

dbtsent evaluate scan must apply ops contracts in this fixed order. Skipping or reordering steps yields alert bundles that disagree with verifier reference math.

1. Read the manifest checkpoint at /app/state/manifest-checkpoint.json and validate seed and bundle against CLI flags.
2. Derive enabled-model topological order using only models where enabled is true. Disabled models never appear in model_order.
3. Evaluate source freshness rows from checkpoint sources and evaluated_at. Apply warn_after_minutes and error_after_minutes with strict greater-than minute boundaries.
4. Walk exposure dependency closure by collecting transitive model dependencies for each exposure depends_on entry.
5. Compute summary counters including stale_source_count and disabled_ref_ok using enabled-model upstream rules from disabled-model-handling.md.
6. Emit alert rows for stale sources, disabled upstream references, and empty exposure closures. Sort alerts by severity, alert_code, then subject_id.
7. Persist the scan payload to /app/work/freshness-scans.db with active replacement semantics for the seed.
8. export alerts reads the persisted scan row plus checkpoint bytes. audit_digest hashes model_order, exposure_refs, normalized alerts, and summary only.

Hidden overlay directory TB3_BUNDLE_DIR may replace bundled packs during evaluate. TB3_FRESHNESS_BIAS_MINUTES adds minutes to every freshness row before status classification.
