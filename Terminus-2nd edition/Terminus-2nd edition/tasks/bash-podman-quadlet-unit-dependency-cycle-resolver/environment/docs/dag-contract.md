# Dependency DAG contract

`quadlet-resolver order` builds a directed graph over unit names from parse output.

## Directed edges

For each unit `U`, examine merged `[Unit]` fields:

- Every name in `After=` that matches another unit in the same tree creates edge **dependency → U** (dependency must start before `U`).
- Every name in `Wants=` that matches another unit in the same tree creates the same directed edge.

Edges are **directed only**. An `After=` or `Wants=` from `A` to `B` does not imply an edge from `B` to `A` unless explicitly listed in `B`'s unit fields.

External targets (for example `network-online.target`) are ignored for ordering among quadlet units.

## Cycle detection

If a directed cycle exists among tree units, `order` exits **2** and prints `cycle:unit1,unit2,...` to stderr (comma-separated, first unit repeats at end).

## Topological order

When acyclic, emit JSON:

```json
{"tree": "/app/fixtures/stack", "order": ["db.service", "redis.service", "..."]}
```

Use Kahn's algorithm. When multiple units are ready, pick the **lexicographically smallest** unit name. Every edge must place its tail before its head in `order`.

## Order command

```text
quadlet-resolver order --tree /app/fixtures/stack --out /app/output/order.json
```

`order` runs parse internally; milestone 1 parse behavior must remain correct.
