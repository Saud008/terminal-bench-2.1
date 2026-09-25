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
    codes := make([]string, len(drug.Aliases))
    for i, a := range drug.Aliases {
        codes[i] = a.Code
    }
    sort.Strings(codes)
    return codes[0]
}
