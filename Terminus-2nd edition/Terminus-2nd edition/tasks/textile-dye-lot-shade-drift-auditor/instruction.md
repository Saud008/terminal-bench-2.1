Task identity 0109557906 defines the engineering problem for textile dye lot shade drift auditor. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Build shadedrift, a Bash and AWK textile dye-lot shade drift auditor on the working baseline under /app. This scientific-computing workflow performs numerical calibration of spectrometer LAB readings against recipe targets, walks batch lineage and rework windows into a shade metrology rollup, and exports a deterministic drift atlas using independent reference math. shadedrift ingests spectrometer LAB readings with recipe sheets, fabric batch lineage, and rework notes from scenario bundles, evaluates each reading against the effective recipe target under version precedence and rework windows into a correlation snapshot, and exports a deterministic drift report JSON without re-reading raw fixtures at export time.

Install shadedrift at /app/bin/shadedrift with these subcommands:

  shadedrift ingest-scenario --scenario <name> --run-id <id>
  shadedrift correlate --run-id <id>
  shadedrift export-report --run-id <id> --output <path>

Spectrometer reading columns and duplicate handling appear in /app/docs/readings-format.md. Recipe version precedence against batch creation epochs appear in /app/docs/recipe-precedence.md. Fabric batch parent lineage and inherited LAB anchors appear in /app/docs/batch-lineage.md. Rework window inclusive bounds and pre/post target selection appear in /app/docs/rework-window.md. CIE76 LAB delta math and drift class thresholds appear in /app/docs/lab-delta-thresholds.md. correlation snapshot schema and correlation digest rules appear in /app/docs/correlation-snapshot-schema.md. Drift report field order and audit digest appear in /app/docs/drift-report-schema.md. Scenario bundle layout and bundled inventory appear in /app/docs/scenario-layout.md. Bundled scenarios include scarlet-base-lot, indigo-rework-window, and mercer-lineage-chain. Bundled scenarios include scarlet-base-lot, indigo-rework-window, and mercer-lineage-chain. Verifier overlay roots for hidden fixtures appear in /app/docs/verifier-overlay-paths.md. Shade metrology reasoning steps appear in /app/docs/engineering-problem-contract.md.

shadedrift ingest-scenario materializes /app/state/shade-correlation/<run_id>.json with scenario metadata and reading rows without delta evaluation. shadedrift correlate fills target LAB fields, delta_e, drift_class, recipe_version, and correlation_digest on that correlation snapshot file. shadedrift export-report reads the correlated correlation snapshot only and writes sorted drift rows plus audit_digest under /app/output/. ingest also appends a readings sha256 line to /app/state/run-registry.jsonl for cross-run batch trace.

Duplicate reading_id lines in a readings TSV keep the last line in file order. Recipe selection picks the recipe_name tied to the batch with the greatest effective_from_epoch that is still less than or equal to the batch created_at_epoch. Nullable target_lab on a batch inherits by walking parent_batch_id links until a non-null anchor is found. Rework notes apply inclusive rework_start_epoch and rework_end_epoch bounds; readings inside the window use the pre-rework recipe target resolved at supersedes_reading_before_epoch. CIE76 delta_e is the Euclidean distance in LAB space. Drift classes map delta_e against warn_delta_e and fail_delta_e from /app/config/shadedrift.json.

A decoy hue sort helper under /app/lib/ is not on the shadedrift hot path. Hidden verifier fixtures may appear under /opt/verifier-fixtures/shadedrift/. Run /app/scripts/reset-state.sh before cross-run verifier cases. Pytest helpers invoke shadedrift through subprocess. Independent contract math lives in tests/shadedrift_contract_math.py.

Pytest contract helpers under /tests use hashlib and random for readings_digest integrity checks and anti-hardcoding spot validation. The shadedrift_runner module invokes /app/bin/shadedrift through subprocess.

Reference helpers for pytest parity live at /app/tools/ref_math.py (math and hashlib).
Verifier state paths include /app/state/shade-correlation/, /app/state/run-registry.jsonl, and /app/output/.

State and output paths used by pytest: /app/state/shade-correlation/, /app/state/run-registry.jsonl, /app/output/, /app/work/tb3-root/, /app/work/ephemeral/, /app/work/rand-root/, /app/config/shadedrift.json, /app/fixtures/scenarios/, /app/scripts/rebuild-shadedrift.sh, /app/scripts/reset-state.sh, and /opt/verifier-fixtures/shadedrift/. Pytest run-id tokens include run-digest, run-export-out, run-partial, run-paths, run-stable, and run-path-contract. Snapshot filenames include run-digest.json, run-export-out.json, run-partial.json, run-paths.json, and run-stable.json.
