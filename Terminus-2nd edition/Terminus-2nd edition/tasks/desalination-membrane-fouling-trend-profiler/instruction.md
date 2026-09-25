Task identity d9f4m8r2 defines the engineering problem for desalination membrane fouling trend profiler. See /app/docs/engineering-problem-contract.md for scope boundaries.

## Operational scope

Coastal SWRO skids lose permeate flux when brine-side pressure rises faster than feed salinity drift predicts. Operators need a ranked fouling trend chronicle that ties membrane element batches, chemical cleaning windows, and temperature-flow normalized differential pressure before scheduling the next CIP cycle.

## Deliverable

Extend the working rotrace Rust service under /app so it publishes deterministic fouling trend chronicle JSON under /app/output/ after processing hourly sensor CSV streams.

## Tool surface

Install rotrace at /app/bin/rotrace. Verbs appear in fixed order: load-readings, bind-cleaning, normalize-ndp, score-trends, publish-chronicle. Flag semantics, buffer directories, NDP normalization, salinity calibration offset sign, inclusive membrane batch hour windows, cleaning baseline reset boundaries, sensor dropout bridging, trend slope classification, and chronicle digest field order live only in /app/docs/cip-scheduling-context.md, /app/docs/pressure-buffer-schema.md, /app/docs/cleaning-buffer-schema.md, /app/docs/ndp-grid-schema.md, /app/docs/trend-scratch-schema.md, /app/docs/flow-temp-ndp-normalization.md, /app/docs/membrane-batch-lineage.md, /app/docs/cleaning-reset-window.md, /app/docs/salinity-calibration-offset.md, /app/docs/sensor-dropout-bridge.md, /app/docs/trend-classification-ladder.md, /app/docs/chronicle-publish-fields.md, /app/docs/fixture-train-catalog.md, and /app/docs/pytest-verifier-primitives.md.

## Fixtures and verification

Bundled RO train scenarios sit under /app/fixtures/ro-trains/. Alternate salinity calibration tables honor TB3_CAL_TABLE. Hidden train bundles honor TB3_FIXTURE_ROOT. Pytest contract math uses Python hashlib per /app/docs/pytest-verifier-primitives.md and tests/brine_ndp_contract.py. CIP scheduling context is in /app/docs/cip-scheduling-context.md. Subprocess CLI driving uses tests/swro_pipeline_driver.py. Chronicle contract cases live in tests/test_brine_chronicle_contract.py, pressure snapshots in tests/test_ro_pressure_snapshots.py, and NDP lattice artifacts in tests/test_membrane_ndp_lattice.py. Hidden RO train traps use tests/test_tb3_ro_train_traps.py. Pytest invokes rotrace through subprocess after cargo rebuild.

Compile rotrace with /usr/local/cargo/bin/cargo build --release --locked from /app and install the binary to /app/bin/rotrace from /app/target/release/rotrace. Run /app/scripts/reset-workspace.sh before cross-run verifier cases.
