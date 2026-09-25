# Dependency ledger staging schema

Every successful `pulumi-dep-export order` run writes `/app/state/dep-ledger.json` **before** serializing the export report. The export stage must read this file; rebuilding adjacency from the stack snapshot in export bypasses staging and is incorrect.

## JSON shape

```json
{
  "stack": "dev",
  "epoch": 1,
  "adjacency_digest": "hex-sha256-of-canonical-adjacency",
  "resources": [ { "...": "Resource objects as in stack-snapshot-format.md" } ],
  "adjacency": {
    "urn:prerequisite": ["urn:dependent"]
  }
}
```

| Field | Meaning |
|-------|---------|
| `stack` | Stack name copied from the parsed snapshot |
| `epoch` | Monotonic run counter per `epoch-persistence.md` |
| `adjacency_digest` | Canonical adjacency fingerprint per `epoch-persistence.md` |
| `resources` | Resource rows after `FlattenComponents` (same order as the snapshot list) |
| `adjacency` | Prerequisite → dependents map per `dependency-contract.md` edge rules |

`adjacency` keys and values are resource URNs. Missing keys mean no outgoing edges. Lists preserve insertion order from graph build.

## Pipeline

1. Parse stack snapshot JSON.
2. `validate.ValidateSnapshot` per `validate-contract.md`.
3. `FlattenComponents` → `BuildAdjacency` → write ledger with epoch and adjacency digest.
4. Load ledger → `TopoOrder` → emit export report JSON via `export.BuildReport(snap, ledgerPath)` (see `/app/docs/module-api-contract.md`).

Topological sort and delete-before-replace adjacency fixes belong in `internal/graph/`; export must not re-invoke `BuildAdjacency` on snapshot data.
