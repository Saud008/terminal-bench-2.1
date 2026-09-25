Task identity f7c2a91e defines the engineering problem for java flink checkpoint barrier skew chronicle. See /app/docs/engineering-problem-contract.md for scope and verifier contracts.

# Flink checkpoint barrier skew chronicle

Build the flink-skew chronicle pipeline on the working Java tree at /app. Flink operations teams collect JobManager checkpoint event JSONL after incidents and need a tool that normalizes the checkpoint timeline, classifies barrier alignment, and emits a JSON report with per-operator skew and misalignment class under the contracts in /app/docs/.

## Pipeline

Binary: /app/bin/flink-skew.jar

| Stage | Command | Primary output |
|-------|---------|----------------|
| load-events | load-events --input DIR --out PATH | /app/state/event_index.json |
| align-barriers | align-barriers --index PATH --out PATH | /app/state/alignment.buffer |
| emit-chronicle | emit-chronicle --buffer PATH --out PATH | /app/output/barrier_skew_chronicle.json |

Rebuild with /app/scripts/rebuild-flink-skew.sh before verifier runs. Reset workspace with /app/scripts/reset-state.sh between cross-run checks.

## Contracts

| Topic | File |
|-------|------|
| CLI verbs and flags | /app/docs/cli_surface.md |
| Checkpoint event JSONL schema | /app/docs/checkpoint-event-schema.md |
| Aligned vs unaligned semantics | /app/docs/alignment-semantics.md |
| Watermark vs barrier precedence | /app/docs/watermark-barrier-precedence.md |
| alignment.buffer layout | /app/docs/alignment-buffer-format.md |
| Chronicle JSON contract | /app/docs/chronicle-output-contract.md |
| Operator graph and subtask mapping | /app/docs/operator-graph-mapping.md |
| Chained operator boundaries | /app/docs/chained-operator-boundaries.md |
| Idempotent load-events | /app/docs/load-events-idempotency.md |

Pytest under /tests drives flink-skew through subprocess helpers in flink_skew_shell_ops.py and compares artifacts to independent reference math in skew_refmath.py. Hidden traps use TB3_FIXTURE_ROOT pointing at /opt/verifier-fixtures/flink_skew_hidden.

Hardcoding /app/output artifacts or editing tests is insufficient.
