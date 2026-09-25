package tombwin

import (
    "os"
    "strconv"

    "github.com/terminus/kcompactctl/internal/model"
)

const DefaultRetentionMs int64 = 600_000

func RetentionMs() int64 {
    if raw := os.Getenv("TB3_TOMB_RETENTION_MS"); raw != "" {
        if v, err := strconv.ParseInt(raw, 10, 64); err == nil && v > 0 {
            return v
        }
    }
    return DefaultRetentionMs
}

func TombstoneEligible(rec model.StagedRecord, partitionHigh int64, windowMs int64) bool {
    if !rec.IsTombstone {
        return false
    }
    floor := partitionHigh - windowMs
    return rec.TimestampMs >= floor
}

func PartitionHighWater(records []model.StagedRecord, part int) int64 {
    var hi int64
    for _, rec := range records {
        if rec.Partition == part && rec.TimestampMs > hi {
            hi = rec.TimestampMs
        }
    }
    return hi
}
