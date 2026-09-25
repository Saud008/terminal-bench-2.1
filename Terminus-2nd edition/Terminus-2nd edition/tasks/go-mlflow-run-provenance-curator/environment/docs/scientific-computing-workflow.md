# Scientific computing workflow

This task is a **scientific-computing** numerical reproducibility simulation over ML experiment run catalogs. Experiment metrology operators reconcile heterogeneous training-run assays into a numerically closed provenance certificate with sealed staging artifacts. The agent extends lineage-depth calibration, metric-epoch monotonicity scoring, model-artifact digest normalization, and feature-dataset version binding on the working baseline under /app so certificate export matches independent reference simulation.

The workflow has three numerical stages tied to documented artifacts:

1. **Hydrate** — normalize a scenario catalog into `/app/state/provenance-staging.json` with monotonic `ingest_seq`, scoped training-run ids, metric epochs, model artifact bodies, and feature-dataset manifests.
2. **Bind closure** — persist the active seed row in `/app/work/provenance.db` with lineage depth, binding flags, and epoch monotonicity witnesses copied from staging.
3. **Publish certificate** — combine staging plus the active curated row into JSON under `/app/output/` with root-first lineage_chain, ordered metric_epochs, normalized artifact digests, dataset binding rows, and a canonical `audit_digest` closure hash.

Reference math must match `/app/docs/experiment-provenance-closure-contract.md` for lineage ordering, digest input normalization, epoch/step/key ordering, manifest pin comparison after optional `TB3_MANIFEST_SALT`, and audit_digest key order.

The internal/decoy compression package is not on the provenance closure hot path.
