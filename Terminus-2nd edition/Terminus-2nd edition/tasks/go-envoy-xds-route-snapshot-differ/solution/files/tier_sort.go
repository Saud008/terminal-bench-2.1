package lischain

import (
    "sort"

    "github.com/terminus/xsnapctl/internal/model"
)

func OrderFilters(filters []model.Filter) []model.Filter {
    var network, http []model.Filter
    for _, f := range filters {
        if f.Type == "network" {
            network = append(network, f)
        } else {
            http = append(http, f)
        }
    }
    sort.Slice(network, func(i, j int) bool { return network[i].Name < network[j].Name })
    sort.Slice(http, func(i, j int) bool { return http[i].Name < http[j].Name })
    return append(network, http...)
}
