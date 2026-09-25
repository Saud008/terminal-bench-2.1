package offsetdup

import (
    "fmt"
    "sort"

    "github.com/terminus/kcompactctl/internal/model"
)

func Collapse(records []model.StagedRecord) []model.StagedRecord {
    buckets := map[string][]model.StagedRecord{}
    for _, rec := range records {
        k := dupKey(rec.Partition, rec.Offset)
        buckets[k] = append(buckets[k], rec)
    }
    keys := make([]string, 0, len(buckets))
    for k := range buckets {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    var out []model.StagedRecord
    for _, k := range keys {
        group := buckets[k]
        best := group[0]
        for _, rec := range group[1:] {
            if rec.TimestampMs > best.TimestampMs {
                best = rec
            } else if rec.TimestampMs == best.TimestampMs && rec.CanonicalKey < best.CanonicalKey {
                best = rec
            }
        }
        out = append(out, best)
    }
    sort.Slice(out, func(i, j int) bool {
        if out[i].Partition != out[j].Partition {
            return out[i].Partition < out[j].Partition
        }
        return out[i].Offset < out[j].Offset
    })
    return out
}

func dupKey(part int, off int64) string {
    return fmt.Sprintf("%d:%d", part, off)
}
