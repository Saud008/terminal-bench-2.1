package lischain

import (
    "sort"

    "github.com/terminus/xsnapctl/internal/model"
)

// OrderFilters orders listener filters for canonical export.
func OrderFilters(filters []model.Filter) []model.Filter {
    out := make([]model.Filter, len(filters))
    copy(out, filters)
    sort.Slice(out, func(i, j int) bool {
        return out[i].Name < out[j].Name
    })
    return out
}
