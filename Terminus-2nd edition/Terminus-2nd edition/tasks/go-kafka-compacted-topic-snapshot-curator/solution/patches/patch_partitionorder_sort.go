package partitionorder

import (
    "sort"

    "github.com/terminus/kcompactctl/internal/model"
)

func OrderRecords(records []model.StagedRecord) []model.StagedRecord {
    out := make([]model.StagedRecord, len(records))
    copy(out, records)
    sort.Slice(out, func(i, j int) bool {
        if out[i].Partition != out[j].Partition {
            return out[i].Partition < out[j].Partition
        }
        return out[i].Offset < out[j].Offset
    })
    return out
}
