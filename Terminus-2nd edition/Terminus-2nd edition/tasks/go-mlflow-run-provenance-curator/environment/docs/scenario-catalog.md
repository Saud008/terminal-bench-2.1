# Scenario catalog

Bundled ML experiment scenario files live under /app/fixtures/scenarios/.

- basic-lineage.json exercises root-first training-run ancestry closure across a short parent chain.
- deep-lineage-bind.json exercises longer model-run lineage closure together with multi-dataset feature binding.
- artifact-digest-tree.json exercises normalized model artifact path hashing and digest ordering.
- metric-epoch-order.json exercises eval metric ordering and epoch monotonic summary checks.
- dataset-pin-mismatch.json exercises partial binding failure when one pinned feature manifest hash does not match.

Runtime-supplied overlay bundles may add additional scenario files through TB3_FIXTURE_DIR, including `tb3-cross-bind.json`, but they follow the same staged ingest, curate bind, and export summary workflow.
