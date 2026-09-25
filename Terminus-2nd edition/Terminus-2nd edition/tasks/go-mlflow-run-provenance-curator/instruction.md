Experiment metrology teams complete a scientific-computing numerical reproducibility closure that turns training-run catalogs under /app/fixtures/ into a deterministic eval summary certificate. This scientific-computing workflow combines numerical simulation of cross-run lineage depth, metric-epoch monotonicity calibration, model-artifact digest normalization, and feature-dataset version binding so mlprov can publish sealed provenance staging and certificate JSON that match independent reference math.

The working mlprov operator CLI and numerical kernels under /app already hydrate experiment catalogs on the baseline under /app. Extend that numerical closure so hydrate materializes a feature-run snapshot at /app/state/provenance-staging.json, bind persists the latest closure row in /app/work/provenance.db, and publish emits a deterministic eval summary certificate to a caller-provided path under /app/output/. Calibration invariants and reference math scope live in /app/docs/scientific-computing-workflow.md and /app/docs/experiment-provenance-closure-contract.md.

Operator contracts for the calibration pipeline:

- /app/docs/scientific-computing-workflow.md — numerical reproducibility workflow and reference math scope
- /app/docs/experiment-operator-commands.md — mlprov subcommands and flags
- /app/docs/experiment-provenance-closure-contract.md — lineage, epoch, digest, and binding closure math
- /app/docs/feature-run-snapshot-schema.md — feature-run snapshot schema
- /app/docs/training-run-lineage-closure.md — training-run lineage closure math
- /app/docs/model-artifact-digest-contract.md — model artifact digest closure
- /app/docs/feature-dataset-binding.md — feature dataset version binding
- /app/docs/provenance-database-schema.md — SQLite persistence layout
- /app/docs/eval-summary-certificate-fields.md — eval summary certificate fields and audit_digest closure
- /app/docs/scenario-catalog.md — bundled scenario coverage expectations
- /app/docs/build-toolchain.md — numerical kernel compile path into mlprov

Bundled experiment scenarios and seeds live under /app/fixtures/. Runtime overlays and manifest-salt adjustments follow the same closure contracts.

Complete hydrate staging, bind closure, and certificate publish so sealed artifacts match independent reference math. Leave /app/docs/, /app/config/, and /app/fixtures/ unchanged.
