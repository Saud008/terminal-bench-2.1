# Kubernetes fleet graph snapshot

Path: /app/state/k8s-fleet-graph.json

Fields: engine, scenario, cluster, fleet_graph_digest.

Each scenario cluster bundle is a fleet manifest snapshot loaded from clusters/SCENARIO/cluster.json.

## fleet_graph_digest

SHA-256 hex digest of compact JSON (no spaces) for object `{"cluster":{...}}`.

The inner `cluster` object includes exactly these keys in this order:

1. `audit_clock_ms` — retention evaluation clock (int64 ms)
2. `default_retention_days` — cluster-wide fallback retention (int)
3. `pvcs` — array sorted ascending by `(namespace, name)`
4. `snapshots` — array sorted ascending by `uid`
5. `storage_classes` — array as loaded from fixture (fixture order preserved)
6. `backup_policies` — array as loaded from fixture (fixture order preserved)
7. `quotas` — array as loaded from fixture (fixture order preserved)

Only the fields above participate in the digest; it is not a hash of the full cluster dump.

The on-disk file also carries the full unsorted `cluster` object for downstream scoring; only the digest payload applies the PVC and snapshot sorts.

cluster.audit_clock_ms is the retention evaluation clock for age calculations.
