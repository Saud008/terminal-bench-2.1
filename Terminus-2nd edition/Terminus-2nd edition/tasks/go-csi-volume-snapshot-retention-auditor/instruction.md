Backup desk operators run the host-local snapretctl snapshot-retention ops desk at `/app/bin/snapretctl`. For each offline scenario, the desk loads a cluster manifest bundle, writes a normalized fleet graph snapshot, scores which volume snapshots may expire under retention rules, and publishes an audit report plus orphan ledger when the score pass counter is positive. There is no live cluster API, CSI driver, or outbound network step. This is a system-administration host-local ops desk (import → score → seal); keep staging files, pass counters, and report export aligned. It is not a generic software-engineering module-repair exercise, security authorization task, or pytest harness.

Ops contracts under `/app/docs/`: `cli-surface.md`, `k8s-fleet-graph-contract.md`, `pvc-join-contract.md`, `class-retention-contract.md`, `dangling-contract.md`, `policy-precedence-contract.md`, `quota-accounting-contract.md`, `volsnap-audit-contract.md`, and `byte-stable-publish-contract.md`.

Primary ops verbs:

```text
snapretctl import-graph --scenario NAME [--fixture-dir PATH]
snapretctl score-retention --scenario NAME
snapretctl publish-audit --scenario NAME
```

`import-graph` reads `clusters/NAME/cluster.json` and writes `/app/state/k8s-fleet-graph.json` including the `fleet_graph_digest` defined in `/app/docs/k8s-fleet-graph-contract.md`. `score-retention` writes `/app/work/scoring-findings.json` and increments `audit_pass` in `/app/state/audit-pass-counter.json`. `publish-audit` writes `/app/output/volsnap-audit-report.json` and `/app/output/orphan-snapshot-ledger.jsonl` only when `audit_pass` is greater than zero.

Retention scoring joins each snapshot to its source PVC by namespace and name, applies storage-class day overrides and namespace backup-policy precedence (Retain policy blocks expiry), and flags namespace quota overruns from summed `restore_size_bytes`.

Module `snapret.decoy` sits off the import-graph, score-retention, and publish-audit pathway and must not influence those stages. Bundled scenarios under `/app/fixtures/clusters` include clean-retention, pvc-join-chain, class-override, dangling-snap, policy-precedence, quota-cap, retain-pin, and stable-republish. When `TB3_FIXTURE_DIR` is set, scenarios load from that root (including `/opt/verifier-fixtures/snapretctl`). When `TB3_CLUSTER_DEFAULT_RETENTION_DAYS` is set, it overrides the cluster default retention days on verifier-only scenarios. After policy-module edits under `/app/lib/snapret/`, leave `/app/bin/snapretctl` current for the graded control plane (the verifier invokes `/app/scripts/verifier-rebuild.sh`). Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
