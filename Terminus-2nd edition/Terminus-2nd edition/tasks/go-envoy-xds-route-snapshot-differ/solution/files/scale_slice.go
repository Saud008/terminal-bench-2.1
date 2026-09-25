package epwscale

import (
    "os"
    "sort"
    "strconv"

    "github.com/terminus/xsnapctl/internal/model"
)

const DefaultScale = 100

func WeightScale() int {
    if raw := os.Getenv("TB3_WEIGHT_SCALE"); raw != "" {
        if v, err := strconv.Atoi(raw); err == nil && v > 0 {
            return v
        }
    }
    return DefaultScale
}

func NormalizeEndpoints(endpoints []model.Endpoint) []model.Endpoint {
    scale := WeightScale()
    if len(endpoints) == 0 {
        return endpoints
    }
    total := 0
    for _, ep := range endpoints {
        total += ep.Weight
    }
    if total == 0 {
        return endpoints
    }
    type item struct {
        host string
        raw  float64
        base int
    }
    items := make([]item, len(endpoints))
    sum := 0
    for i, ep := range endpoints {
        raw := float64(scale*ep.Weight) / float64(total)
        base := int(raw)
        items[i] = item{host: ep.Host, raw: raw, base: base}
        sum += base
    }
    rem := scale - sum
    order := make([]int, len(items))
    for i := range order {
        order[i] = i
    }
    sort.Slice(order, func(i, j int) bool {
        return items[order[i]].raw-float64(items[order[i]].base) >
            items[order[j]].raw-float64(items[order[j]].base)
    })
    for i := 0; i < rem && i < len(order); i++ {
        items[order[i]].base++
    }
    out := make([]model.Endpoint, len(items))
    for i, it := range items {
        out[i] = model.Endpoint{Host: it.host, Weight: it.base}
    }
    return out
}
