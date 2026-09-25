Diagnose and fix bugs in the existing Rust wheel-resolution modules under /app/environment so the offline PyPI-style resolver CLI evaluates dependency pins, constraint specifiers, and wheel tag compatibility correctly. The CLI loads scenario bundles, materializes a normalized resolution snapshot at /app/state/whres-snapshot.json, and writes a deterministic wheel candidate report JSON to a caller-provided output path.

Install the resolver at the path in /app/docs/cli-surface.md with these subcommands:

  load --scenario <name> --run-id <id>
  analyze --run-id <id>
  emit --run-id <id> --output <path>

PEP 440 version rank ladder including epoch, tilde pre-releases, post and local segments follow /app/docs/pep440-version-order.md. Environment marker evaluation for requires_python and requires_dist strings follow /app/docs/environment-marker-rules.md. Wheel tag compatibility including abi3 fallbacks follow /app/docs/wheel-tag-compatibility.md. Yanked release exclusion from candidate pools follow /app/docs/yanked-release-policy.md. Version specifier matching for query constraints follow /app/docs/constraint-specifiers.md.

The analyze subcommand materializes the resolution snapshot for a run id and writes it to /app/state/whres-snapshot.json before emit. Snapshot schema, index_fingerprint, marker_env, and snapshot_digest rules appear in /app/docs/snapshot-resolution-schema.md. The emit subcommand reads the resolution snapshot only and writes sorted wheel candidate rows plus summary counters and audit_digest to the caller-provided output path. Row sort order, reason codes, and audit_digest rules appear in /app/docs/candidate-emit-contract.md.

Resolver ladder precedence for overlapping wheel rows appears in /app/docs/pep440-resolution-ladder.md. Dependency build contract and reproducible snapshot rules appear in /app/docs/dependency-resolution-build-contract.md. Bundled scenario names, fixture paths, package literals, and reason codes appear in /app/docs/scenario-catalog.md. Default bundled scenarios live under /app/fixtures/scenarios/. Alternate scenario roots honor WHRES_SCENARIO_ROOT (load must read scenario bundles from that overlay root when set). Hidden verifier scenario packs may mount under /opt/verifier-fixtures/whres/. Rebuild with /app/scripts/rebuild-whres.sh after changing Rust sources. Run /app/scripts/reset-state.sh before starting a fresh resolution run when prior state must not leak. The metrics decoy module is not on the load or emit hot path.

Success looks like: load creates durable work state for a run id (including when WHRES_SCENARIO_ROOT points at an overlay), analyze writes a schema-valid snapshot with matching snapshot_digest at the path in /app/docs/snapshot-resolution-schema.md, and emit produces a report whose candidate rows, counters, and audit_digest match /app/docs/candidate-emit-contract.md for that snapshot alone.
