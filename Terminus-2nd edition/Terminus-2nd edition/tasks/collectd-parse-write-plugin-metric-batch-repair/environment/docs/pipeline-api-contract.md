# Pipeline module API contract

`internal/pipeline` orchestrates `collectdctl stage`, `export`, and `ingest`. Repairs focus on `internal/parse`, `internal/normalize`, `internal/flush`, `internal/staging`, and `internal/export`, but **`pipeline.go` must keep stable cross-package call sites** so partial module swaps still compile.

The shipped starter template under `/app/internal/pipeline/pipeline.go` defines the only cross-package calls `pipeline.go` may make. When fixing `Export` (or any other path), **do not add, remove, or rename cross-package function calls** in `pipeline.go`. Repair behavior inside the other packages; keep `ingestBatches` and the stage/export orchestration call graph identical to the starter.

## Required call sites in `internal/pipeline`

| Caller | Callee | Required signature |
|--------|--------|-------------------|
| `pipeline.Stage` | `staging.Write` | `func Write(report model.Report) error` |
| `pipeline.Export` | `staging.Read` | `func Read() (staging.Envelope, error)` |
| `pipeline.Export` | `staging.Verify` | `func Verify(env staging.Envelope) error` |
| `pipeline.Export` | `export.Write` | `func Write(path string, env staging.Envelope) error` |
| `ingestBatches` | `parse.ParseStream` | `func ParseStream(content string) ([]model.RawReading, error)` |
| `ingestBatches` | `normalize.ExpandReadings` | `func ExpandReadings(raw model.RawReading, typesDB map[string]map[string]string) []model.NormalizedPoint` |
| `ingestBatches` | `flush.WithinSkew` | `func WithinSkew(epoch, anchor, skewSec int64) bool` |
| `ingestBatches` | `parse.TypeName` | `func TypeName(identifier string) string` |
| `ingestBatches` | `normalize.PairRates` | `func PairRates(points []model.NormalizedPoint, kind string) []model.NormalizedPoint` |
| `ingestBatches` | `flush.FlushIndex` | `func FlushIndex(epoch, origin, intervalSec int64) int64` |
| `ingestBatches` | `flush.FlushBounds` | `func FlushBounds(index, origin, intervalSec int64) (start, end int64)` |

Do **not** rename `export.Write` or change its parameters (for example to `WriteReport(path string, report model.Report)`). `pipeline.Export` must call `export.Write(outPath, env)` with the envelope returned by `staging.Read()` after `staging.Verify` succeeds.

## `ingestBatches` locked call surface

`BuildReport` and (in the broken starter only) a mistaken `Export` re-ingest path both funnel through `ingestBatches`. That function must continue to call **exactly** these package-level symbols — no helpers added in `pipeline.go`, and no substitute parse/normalize/flush entry points:

1. **`parse.ParseStream(content)`** — once per batch body; drives line counts in `report.stats`.
2. **`normalize.ExpandReadings(raw, cfg.TypesDB)`** — once per raw reading from the stream.
3. **`flush.WithinSkew(pt.Epoch, anchor, cfg.TimeSkewSec)`** — per expanded point after epoch-origin filtering.
4. **`parse.TypeName(key.id)`** — when resolving the value kind from `cfg.TypesDB` for each series bucket.
5. **`normalize.PairRates(pts, kind)`** — after grouping points by canonical id and DS name.
6. **`flush.FlushIndex(pt.Epoch, cfg.EpochOrigin, cfg.FlushIntervalSec)`** — per normalized point before flush assignment.
7. **`flush.FlushBounds(idx, cfg.EpochOrigin, cfg.FlushIntervalSec)`** — when materializing each `model.FlushExport` window.

Do **not** call package-private helpers (for example `parse.ParseLine`, `normalize.CanonicalID`, or `parse.readIdentifier`) from `pipeline.go`. Those may change during repairs in their home packages; only the exported symbols above are part of this contract.

## Export must not re-ingest

`pipeline.Export` must publish the staged `env.Report` through `export.Write`. It must **not** re-read PUTVAL batch files or call `BuildReport` / `ingestBatches` during export. Staging snapshot rows — including metric order and values — are authoritative for export output.

The correct `Export` body is: `staging.Read` → `staging.Verify` → `export.Write(outPath, env)` → return. Removing the broken starter’s batch re-read and `ingestBatches` call satisfies export behavior **without** altering any `ingestBatches` call site listed above.

## Partial-fix builds

The verifier may replace individual files under `/app/internal/` with broken originals while keeping your `pipeline.go`, then rebuild `collectdctl`. Only the golden copy of each patched module is swapped in; unpatched modules stay broken. If `pipeline.go` references symbols that exist only in your repaired modules (new parse/normalize/flush helpers, renamed entry points, or extra cross-package calls), those builds fail to compile even when ingest logic elsewhere is correct.

Keeping every signature in the table above — and **only** those cross-package calls in `ingestBatches` — ensures partial-fix builds remain linkable when `pipeline.go` still references the starter call graph.
