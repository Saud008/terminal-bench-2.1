package docketdedup

import (
    "sort"
    "strings"

    "github.com/terminus/filingatlas/internal/model"
)

func PickPrimaryDocket(dockets []model.Docket) string {
    if len(dockets) == 0 {
        return ""
    }
    for _, d := range dockets {
        if d.PrimaryFlag {
            return strings.TrimSpace(d.Number)
        }
    }
    sorted := append([]model.Docket{}, dockets...)
    sort.Slice(sorted, func(i, j int) bool {
        return sorted[i].FiledAt > sorted[j].FiledAt
    })
    return strings.TrimSpace(sorted[0].Number)
}
