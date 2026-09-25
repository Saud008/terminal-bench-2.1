# Internal module API contract

The `order` command in `/app/internal/replay/order.go` wires snapshot validation, graph build, ledger staging, topological sort, and export serialization. Partial-fix verifiers compile replacement Go modules into `/app/internal/graph/`, `/app/internal/export/`, `/app/internal/validate/`, and `/app/internal/replay/` while keeping these exported surfaces compatible.

## Validation stage

Package: `/app/internal/validate/`

| Symbol | Signature | Called from |
|--------|-----------|-------------|
| `ValidateSnapshot` | `func ValidateSnapshot(snap model.Snapshot) error` | `replay.OrderStack` before graph build |

## Export stage (stable)

Package: `/app/internal/export/`

| Symbol | Signature | Called from |
|--------|-----------|-------------|
| `BuildReport` | `func BuildReport(snap model.Snapshot, ledgerPath string) model.ExportReport` | `replay.OrderStack` after `graph.WriteLedger` |

**Do not rename `BuildReport`, remove parameters, or change parameter types.** Fix serialization inside the function body (load the ledger, call `graph.TopoOrder` on ledger rows, populate export fields). A ledger-only export helper with a different signature is incorrect unless `order.go` is updated to match — the shipped CLI keeps the two-argument form above.

Export must read adjacency from `ledgerPath` (`/app/state/dep-ledger.json` per run). Rebuilding adjacency from the raw snapshot inside export bypasses staging and violates `/app/docs/dependency-contract.md`.

## Graph stage (stable names)

Package: `/app/internal/graph/`

| Symbol | Role |
|--------|------|
| `FlattenComponents(resources []model.Resource) []model.Resource` | Component parent flattening before graph build |
| `BuildAdjacency(resources []model.Resource) map[string][]string` | Prerequisite → dependents adjacency |
| `WriteLedger(path, stack, resources, adj) error` | Persist staging artifact with epoch and adjacency digest |
| `LoadLedger(path) (Ledger, error)` | Read staging artifact for sort/export |
| `TopoOrder(resources []model.Resource, adj map[string][]string) []string` | Kahn sort with snapshot-index tie-break |

Fix edge rules, tie-breaking, and delete-before-replace handling in the bodies of these functions. Do not replace them with differently named entry points that partial verifiers cannot swap in.

## Model types

Shared structs in `/app/internal/model/` (`Snapshot`, `Resource`, `ExportReport`, `OrderEntry`, etc.) follow JSON field names in `/app/docs/export-schema.md` and `/app/docs/stack-snapshot-format.md`. Do not rename exported struct fields or JSON tags when repairing graph or export logic.
