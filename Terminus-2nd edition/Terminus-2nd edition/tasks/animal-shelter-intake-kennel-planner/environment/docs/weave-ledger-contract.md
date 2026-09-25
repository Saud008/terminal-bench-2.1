# Weave ledger contract

weave writes /app/work/quarantine-weave-clean-intake.jsonl audit lines and /app/work/quarantine-weave-clean-intake.header.json summary with placements, transfers, run_stamp, weave_pass for the bundled clean-intake scenario. Other run-id values substitute for clean-intake in both paths.

weave increments weave_pass in /app/state/weave-pass-clean-intake.json on each successful weave.

JSONL lines include kind placement or transfer, animal_id, kennel_id or partner species, and penalty cents when applicable.

Header placements and transfers arrays must match JSONL row counts.
