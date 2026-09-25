package lifecycle

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func FilterStale(allocs []model.ScopedAllocation, cutoff uint64) ([]model.ScopedAllocation, int) {
	active := make([]model.ScopedAllocation, 0, len(allocs))
	suppressed := 0
	for _, a := range allocs {
		if a.SupersededBy != "" {
			suppressed++
			continue
		}
		if a.ModifyIndex < cutoff {
			suppressed++
			continue
		}
		active = append(active, a)
	}
	return active, suppressed
}
