package epwscale

import "github.com/terminus/xsnapctl/internal/model"

func WeightScale() int {
    return 100
}

// NormalizeEndpoints scales endpoint weights to integers summing to scale.
func NormalizeEndpoints(endpoints []model.Endpoint) []model.Endpoint {
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
    out := make([]model.Endpoint, len(endpoints))
    for i, ep := range endpoints {
        out[i] = model.Endpoint{
            Host:   ep.Host,
            Weight: (ep.Weight * WeightScale()) / total,
        }
    }
    return out
}
