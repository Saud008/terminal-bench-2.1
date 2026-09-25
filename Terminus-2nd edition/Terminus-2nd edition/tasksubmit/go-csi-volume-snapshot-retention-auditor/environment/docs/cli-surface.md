# snapretctl CLI surface

Fixed verb order: import-graph, analyze, publish-audit.

Binary path: /app/bin/snapretctl

## import-graph

snapretctl import-graph --scenario SCENARIO [--fixture-dir DIR]

Reads clusters/SCENARIO/cluster.json and writes the fleet graph at /app/state/k8s-fleet-graph.json

## analyze

snapretctl score-retention --scenario SCENARIO

Writes /app/work/scoring-findings.json and increments the pass counter at /app/state/audit-pass-counter.json

## publish-audit

snapretctl publish-audit --scenario SCENARIO [--output-report PATH] [--output-dangling PATH]

Blocked when audit_pass_seq is zero. Default report path /app/output/volsnap-audit-report.json and ledger path /app/output/orphan-snapshot-ledger.jsonl

internal/decoy/yamlutil is not authoritative for publish-audit output.
