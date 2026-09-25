# Isolation overlay contract

Verifier runs may set `TB3_FIXTURE_DIR` (default `/opt/verifier-fixtures/wireclock`). Before pytest, the harness copies golden and stub Go modules into that directory. Isolation cases temporarily replace selected baseline files under `/app/pkg/` with modules from `TB3_FIXTURE_DIR`, rebuild `wireclock`, then restore the tree.

## What the overlay swaps

Baseline package files (the only files isolation may replace in place):

| Package | Baseline files |
|---------|----------------|
| `pkg/objclock` | `types.go`, `codec.go`, `bsonwire.go`, `generator.go` |
| `pkg/digestseal` | `snapshot.go` |
| `pkg/oidstore` | `commit.go` |
| `pkg/intakegate` | `service.go` |
| `pkg/srcursor` | `by_path.go` |
| `pkg/jsonlresume` | `apply.go` |

During an overlay, any extra agent-added `*.go` files in those packages are removed so they cannot clash with the staged golden stubs, then restored afterward. Unlisted packages such as `pkg/httpsurf` are never swapped; they keep calling the exported APIs below.

## Stable exported API surface

Partial overlays compile only when cross-package call sites keep these exported names and signatures. Renaming them (for example `Mint` instead of `Generate`, or `NewPlayer` instead of `NewReplayer`) breaks `pkg/httpsurf` and the golden overlay modules even when behavioral logic is correct.

| Package | Required exported symbols |
|---------|---------------------------|
| `pkg/objclock` | `NewGenerator(machineID string) *Generator`, `(*Generator) BindMachine(machineID string)`, `(*Generator) Generate(nowUnix int64) (ID, error)`, `ParseHex`, `MarshalDocument`, `ID.Hex` |
| `pkg/jsonlresume` | `NewReplayer(db *durastore.DB, gen *objclock.Generator) *Replayer`, `(*Replayer) Replay(path string) (int, error)` |
| `pkg/intakegate` | `NewService(db *durastore.DB, gen *objclock.Generator, machineID string) *Service`, `(*Service) AdmitBatch(nowUnix int64, docs []Document) ([]Result, error)` |
| `pkg/digestseal` | `WriteBatchSnapshot`, `LoadBatchSnapshot`, `ComputeBatchDigest`, `BatchSnapshotPath`, `BatchDocument` |
| `pkg/oidstore` | `CommitBatch`, `ToSealDocs` |
| `pkg/srcursor` | `LoadAppliedLines`, `RecordApplied`, `ReplayPathCursorPath` |

Repair behavior inside these packages; keep the exported entry points listed above so isolation overlays remain linkable.
