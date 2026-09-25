package latestmap

import (
    "github.com/terminus/kcompactctl/internal/model"
    "github.com/terminus/kcompactctl/internal/tombwin"
)

type CompactResult struct {
    Rows    []model.SnapshotRow
    Lineage []model.LineageRow
}

func ComposeTable(records []model.StagedRecord, windowMs int64) CompactResult {
    latest := map[string]model.StagedRecord{}
    for _, rec := range records {
        latest[rec.CanonicalKey] = rec
    }
    var rows []model.SnapshotRow
    for ck, rec := range latest {
        deleted := rec.IsTombstone
        val := rec.ValueRaw
        if deleted {
            val = ""
        }
        rows = append(rows, model.SnapshotRow{
            CanonicalKey: ck,
            Partition:    rec.Partition,
            Offset:       rec.Offset,
            ValueRaw:     val,
            Deleted:      deleted,
        })
        _ = ck
    }
    var lineage []model.LineageRow
    byPart := map[int][]model.StagedRecord{}
    for _, rec := range records {
        byPart[rec.Partition] = append(byPart[rec.Partition], rec)
    }
    for part, partRecs := range byPart {
        hi := tombwin.PartitionHighWater(records, part)
        for _, rec := range partRecs {
            if tombwin.TombstoneEligible(rec, hi, windowMs) {
                lineage = append(lineage, model.LineageRow{
                    CanonicalKey: rec.CanonicalKey,
                    Partition:    rec.Partition,
                    Offset:       rec.Offset,
                    TimestampMs:  rec.TimestampMs,
                })
            }
        }
    }
    return CompactResult{Rows: rows, Lineage: lineage}
}
