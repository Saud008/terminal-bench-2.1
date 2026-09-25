Metrology compliance operators must implement calbind on the working Rust baseline under /app. calbind assembles a calibration chain dossier from instrument readings, calibration certificates, reference-standard traceability links, technician authorization records, and uncertainty budgets using a three-phase ingest, fuse, and export workflow.

Install calbind at /app/bin/calbind from /app/target/release/calbind with exactly three subcommands:

  calbind ingest --batch <batch-id> --pack <name>
  calbind fuse --batch <batch-id>
  calbind export --batch <batch-id> --output <path>

calbind ingest loads the named calibration run pack, validates certificate validity, walks reference-standard parent links, propagates combined standard uncertainty from budget components, checks technician scope against the instrument id, evaluates asymmetric tolerance on each reading channel, and writes an intake vault snapshot at /app/state/intake-vault.json keyed by batch id. Vault field contracts appear in /app/docs/intake-vault-schema.md.

calbind fuse reads the intake vault for the batch id and upserts the latest fused instrument row into /app/work/calibration-register.db. fuse_generation monotonicity and register column layout appear in /app/docs/calibration-register-contract.md. A subsequent fuse for the same batch supersedes the prior active row even when the pack name changes.

calbind export reads only the register row for the batch id and writes dossier JSON to the requested output path. Export row ranking, summary counters, and dossier_digest binding appear in /app/docs/metrology-dossier-export.md.

Certificate hash composition follows /app/docs/certificate-validity-rules.md. Reference-standard traceability parent resolution follows /app/docs/standard-traceability-chain.md. Combined uncertainty propagation follows /app/docs/uncertainty-budget-propagation.md. Technician instrument scope authorization follows /app/docs/technician-authorization-scope.md. Asymmetric tolerance band decisions follow /app/docs/tolerance-decision-matrix.md. The intake-fuse-export boundary appears in /app/docs/metrology-chain-workflow.md.

Calibration run packs and batch pools live under /app/fixtures/cal_runs/. The bundled inventory and behaviors each pack exercises appear in /app/docs/run-pack-catalog.md. Runtime-supplied pack overlays follow those same contracts.

Compile calbind with /usr/local/cargo/bin/cargo build --release from /app. Independent verifier contract math lives in /app/scripts/metrology_contract_math.py. Pytest helpers for subprocess CLI invocation live in /app/scripts/calbind_harness.py. Run /app/scripts/reset-workspace.sh before cross-run verifier cases. The decoy spectrum plotter module is not used by ingest, fuse, or export.
