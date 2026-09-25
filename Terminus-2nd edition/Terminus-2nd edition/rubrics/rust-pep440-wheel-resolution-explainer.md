# Platform rubric — rust-pep440-wheel-resolution-explainer

**Task folder:** tasks/rust-pep440-wheel-resolution-explainer/

Agent loads scenario bundles into work files with whres load, +2
Agent materializes resolution snapshot JSON with index_fingerprint and snapshot_digest, +3
Agent evaluates environment markers numerically for requires_python clauses, +3
Agent ranks PEP 440 versions with epoch tilde post and local segments, +3
Agent matches version specifiers for constraint queries per contract, +3
Agent selects compatible wheel tags including abi3 fallbacks, +3
Agent excludes yanked index rows from candidate pools, +3
Agent emits sorted candidate rows with audit_digest from snapshot only, +3
Agent preserves query rows and target env fields in snapshot schema, +2
Agent reads hidden verifier scenarios via WHRES_SCENARIO_ROOT overlay, +2
Agent runs /app/scripts/rebuild-whres.sh before invoking /app/bin/whres, +1
Agent leaves tag_metric_decoy off load and emit hot path, +1
Agent compares python_version markers lexicographically as strings, -3
Agent selects wheel tag without abi3 fallback on newer CPython, -3
Agent includes yanked releases in export candidate selection, -3
Agent computes snapshot_digest without target env in hash input, -3
Agent breaks PEP 440 tie by first index row instead of highest version, -3
Agent recomputes emit rows from fixture indexes instead of reading the snapshot, -3
