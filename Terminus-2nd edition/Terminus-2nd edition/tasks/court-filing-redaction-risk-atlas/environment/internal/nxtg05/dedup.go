package docketdedup

import (
    "sort"
    "strings"

    "github.com/terminus/filingatlas/internal/model"
)

// PickPrimaryDocket selects the docket row for a scenario bundle.
func PickPrimaryDocket(dockets []model.Docket) string {
    if len(dockets) == 0 {
        return ""
    }
    sorted := append([]model.Docket{}, dockets...)
    sort.Slice(sorted, func(i, j int) bool {
        return sorted[i].FiledAt > sorted[j].FiledAt
    })
    return strings.TrimSpace(sorted[0].Number)
}
