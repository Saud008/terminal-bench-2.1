Evacuation zone alert playtest

Build the evacuation zone alert playtest, an offline wildfire-hazard playfield planner for zone-fire overlap admission, closed-road detours, shelter-quota traps, and sealed alert-bundle win conditions on the working baseline under `/app`. The planner loads county scenario packs, applies polygon intersection and ray-cast containment scoring, audits closed-edge routing and shelter capacity traps, then seals weave-ledger and alert-bundle playtest exports when the alert-bundle win condition is met. This is a games evacuation-zone playtest and sealed-ledger workflow: keep flat-kilometer geometry, true polygon intersection (not bbox-only), closed-segment routing, shelter quota decrements, severity-tier precedence, staged weave snapshots, and sealed alert-bundle exports aligned. It is not a scientific-computing research notebook, generic Rust CLI engineering, debugging, security admission, data-processing pipeline, or CI tooling exercise.

k7cal is available at `/app/bin/k7cal`. Subcommands and flags are cataloged under `/app/docs/`:

  bind
  weave
  seal

`k7cal bind --scenario NAME --run-id ID` admits one scenario pack from `/app/fixtures/scenarios/` (or an overlay root) and binds it to the run id.

`k7cal weave --run-id ID` writes the playfield weave ledger at `/app/state/evac-lane-ledger.json` including calibrated zone-fire intersection rows, routed shelter assignments, and weave_digest.

`k7cal seal --run-id ID --output PATH` seals alert-bundle playtest JSON at the caller-provided `--output` path under `/app/output/` only from that staged weave ledger. Bundles sort by descending severity urgency (lower numeric rank first) then ascending zone_id, and include summary counters, bundle_digest, and weave_digest.

Playfield contracts live under `/app/docs/` (`evac-playtest-workflow.md`, `cli-surface.md`, `coordinate-geometry-contract.md`, `fire-zone-intersection-contract.md`, `road-closure-routing-contract.md`, `shelter-quota-contract.md`, `severity-precedence-contract.md`, `alert-bundle-schema.md`, `lane-ledger-schema.md`, `output-bundle-contract.md`, `digest-contract.md`, `scenario-catalog.md`). Bundled scenario packs live under `/app/fixtures/scenarios/`. Alternate roots honor `EVAC_SCENARIO_ROOT` and `TB3_FIXTURE_DIR`. Hidden verifier packs may mount under `/opt/verifier-fixtures/k7cal/`. The decoy weather module stays outside the bind / weave / seal playtest hot path. Do not modify `/app/docs/` or `/app/fixtures/`. Offline only.
