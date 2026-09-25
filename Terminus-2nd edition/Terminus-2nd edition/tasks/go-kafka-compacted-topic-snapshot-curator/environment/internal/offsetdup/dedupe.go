package offsetdup

import (
    "fmt"

    "github.com/terminus/kcompactctl/internal/model"
)

func Collapse(records []model.StagedRecord) []model.StagedRecord {
    seen := map[string]bool{}
    var out []model.StagedRecord
    for _, rec := range records {
        key := fmt.Sprintf("%d:%d", rec.Partition, rec.Offset)
        if seen[key] {
            continue
        }
        seen[key] = true
        out = append(out, rec)
    }
    return out
}
