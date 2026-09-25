cadence-replay replay --scenario PATH --output /app/output/workflow-replay-report.json --state /app/state/cadence-task-state.json

cadence-replay dump-report --output /app/output/workflow-replay-report.json

Exit code 0 on success. Missing --scenario exits 2. Parse errors exit 1.
