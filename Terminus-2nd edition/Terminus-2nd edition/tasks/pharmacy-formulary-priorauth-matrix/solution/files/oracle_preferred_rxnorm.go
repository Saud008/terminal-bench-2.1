package formndc

import (
    "sort"

    "github.com/terminus/formulatrix/internal/model"
)

func PreferredRxNorm(drug model.Drug) string {
    if drug.RxNorm != "" {
        return drug.RxNorm
    }
    if len(drug.Aliases) == 0 {
        return ""
    }
    bestRank := drug.Aliases[0].Rank
    for _, a := range drug.Aliases {
        if a.Rank > bestRank {
            bestRank = a.Rank
        }
    }
    var top []string
    for _, a := range drug.Aliases {
        if a.Rank == bestRank {
            top = append(top, a.Code)
        }
    }
    sort.Strings(top)
    return top[0]
}
