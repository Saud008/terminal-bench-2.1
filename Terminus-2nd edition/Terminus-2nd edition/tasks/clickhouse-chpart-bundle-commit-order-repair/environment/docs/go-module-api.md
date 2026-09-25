# Go module API stability

Refactors must preserve the exported function and method names and parameter lists below. Localized edits must still compile as a single module; renaming symbols or changing signatures breaks callers even when behavior is otherwise correct.

## ingest package

| Symbol | Signature |
|--------|-----------|
| RegisterPart | func RegisterPart(st *store.Store, meta model.PartMeta) error |
| ApplyChecksum | func ApplyChecksum(st *store.Store, partID string, ok bool) error |
| ShouldSkipReplay | func ShouldSkipReplay(st *store.Store, key string) (bool, error) |
| RecordReplay | func RecordReplay(st *store.Store, key, partID string) error |
| IngestKey | func IngestKey(batchID, partID string) string |
| Run | func Run(partsDir, cfgPath, dbPath string) error |

Package-private checksumFail(partID string) error must remain available to ingest.Run for checksum rejection.

## store package

| Symbol | Signature |
|--------|-----------|
| RegisterPart | func (s *Store) RegisterPart(meta model.PartMeta, committed bool) error |
| MarkChecksumOK | func (s *Store) MarkChecksumOK(partID string, ok bool) error |
| RecordIngestKey | func (s *Store) RecordIngestKey(key, partID string) error |
| HasIngestKey | func (s *Store) HasIngestKey(key string) (bool, error) |
| FinalizeCommit callers | SetMaxBlock, SetFsynced, CommitState signatures unchanged |

## staging package

| Symbol | Signature |
|--------|-----------|
| WriteEarlyManifest | func WriteEarlyManifest(snap model.Snapshot) error |
| WriteSnapshot | func WriteSnapshot(snap model.Snapshot) error |

## merge, commit, ttl, export

| Package | Symbol | Signature |
|---------|--------|-----------|
| merge | MergeRows | func MergeRows(rows []model.Row) []model.MergedRow |
| commit | FinalizeCommit | func FinalizeCommit(st *store.Store, maxBlock int64) error |
| ttl | PruneMerged | func PruneMerged(rows []model.MergedRow, graceMS int64) []model.MergedRow |
| export | WriteReport | func WriteReport(output string) error |

Behavior may change inside these functions; names and parameters must not.
