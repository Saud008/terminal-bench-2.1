Orchard agronomy metrology teams complete a scientific-computing moisture-deficit calibration closure that turns orchard field packs under /app/fixtures/orchards/ into a deterministic irrigation plan. This scientific-computing workflow combines numerical simulation of soil-probe calibration offsets, root-zone volumetric depth conversion, crop-stage Kc lookup, area-weighted probe blending, evapotranspiration demand scoring, district quota carryover, and pump capacity ceilings so veldt-cli can publish sealed moisture ledgers and irrigation plan JSON that match independent reference math.

The working veldt-cli operator CLI and numerical agronomy kernels under /app/environment already hydrate orchard packs on the baseline under /app. Extend that numerical closure so load-pack admits a field pack, build-ledger materializes a calibrated moisture ledger at /app/state/moisture-ledger.json, and publish-plan emits a deterministic irrigation plan JSON to a caller-provided path under /app/output/. Calibration invariants and reference math scope live in /app/docs/scientific-computing-workflow.md.

Operator contracts for the calibration pipeline:

- /app/docs/scientific-computing-workflow.md — agronomy deficit workflow and reference math scope
- /app/docs/probe-calibration-contract.md — probe calibration offsets and volumetric water content normalization
- /app/docs/root-zone-depth-contract.md — root-zone depth conversion from volumetric fraction to millimeters
- /app/docs/crop-stage-kc-curve.md — crop-stage crop coefficient lookup
- /app/docs/probe-blend-contract.md — area-weighted probe blending for a field
- /app/docs/deficit-scoring-contract.md — evapotranspiration demand and moisture deficit scoring
- /app/docs/quota-window-carryover.md — district quota windows with carryover
- /app/docs/pump-capacity-contract.md — pump liters per slot ceiling
- /app/docs/moisture-ledger-schema.md — moisture ledger schema and ledger_digest rules
- /app/docs/irrigation-plan-schema.md — irrigation plan field order and plan_digest rules
- /app/docs/orchard-scenario-catalog.md — bundled orchard scenario coverage

veldt-cli load-pack --orchard <name> --run-id <id> admits an orchard field pack from the active scenario root. veldt-cli build-ledger --run-id <id> writes the moisture ledger including per-field calibrated readings, per-window ET demand millimeters, and ledger_digest. veldt-cli publish-plan --run-id <id> --output <path> reads the moisture ledger only and writes irrigation assignments sorted by field_id then window_index, quota_ledger rows, per-field deficit trace rows, summary counters, and plan_digest.

Binary path: /app/bin/veldt-cli. Bundled orchard scenarios live under /app/fixtures/orchards/. Alternate orchard roots honor ORCHARD_SCENARIO_ROOT. Hidden verifier orchard packs may mount under /opt/verifier-fixtures/irrctl/. Pytest helpers in tests/irrctl_subprocess_helpers.py invoke veldt-cli through subprocess after cargo rebuild. Independent plan math lives in tests/irrctl_plan_math.py. Run /app/scripts/reset-state.sh before cross-run verifier cases. The canopy_shade decoy module is not on the veldt-cli hot path. Do not edit /app/docs/ or /app/fixtures/.
