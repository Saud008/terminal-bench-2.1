# Kubernetes fleet graph snapshot

Path: /app/state/k8s-fleet-graph.json

Fields: engine, scenario, cluster, fleet_graph_digest.

Each scenario cluster bundle is a fleet manifest snapshot: namespaces, PVCs, VolumeSnapshots, storage classes, backup policies, and quota limits loaded from clusters/SCENARIO/cluster.json.

fleet_graph_digest is SHA-256 hex of deterministic JSON object with key cluster where cluster.snapshots and cluster.pvcs are sorted by uid or namespace+name before digest.

cluster.audit_clock_ms is the retention evaluation clock for age calculations.
