# CLI surface

tmpfiles-replay apply --scenario NAME --seed SEED --now EPOCH_SEC [--export PATH]

Runs one apply pass for fixtures/scenarios/NAME. Default export path is /app/output/apply.json. TB3_CLOCK_EPOCH overrides --now when set to an absolute epoch.

tmpfiles-replay generate --scenario NAME --mode boot|boot-ex [--export-rules PATH]

Merges fragments for NAME and writes generate export JSON (default /app/output/generate.json).

Reset work/output with /app/scripts/reset-state.sh before manual runs.
