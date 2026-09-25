# Fixture catalog

Bundled workspaces under /app/fixtures/workspaces:

| workspace_id | scenario |
|--------------|----------|
| baseline | clean serde and libc vendor tree |
| license-drift | declared Apache-2.0 vs resolved MIT |
| checksum-mismatch | stale .cargo-checksum.json package field |
| patched-lineage | patch.crates-io path override |
| duplicate-versions | two bitflags versions in lock |

Hidden workspaces under /opt/verifier-fixtures/tb3-workspaces:

| workspace_id | scenario |
|--------------|----------|
| tb3-precedence-trap | license-file overrides LICENSE star files |
| tb3-staging-poison | export must not re-ingest poisoned vendor |

The decoy script at /app/decoy/cargo-metadata-query.sh is diagnostic only and not on the export hot path.
