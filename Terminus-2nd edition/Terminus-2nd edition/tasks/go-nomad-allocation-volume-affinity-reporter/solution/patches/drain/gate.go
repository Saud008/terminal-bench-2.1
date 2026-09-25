package drain

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func FilterEligible(allocs []model.ScopedAllocation) ([]model.ScopedAllocation, int) {
	eligible := make([]model.ScopedAllocation, 0, len(allocs))
	excluded := 0
	for _, a := range allocs {
		if a.ClientStatus == "down" || a.DesiredStatus == "stop" {
			excluded++
			continue
		}
		eligible = append(eligible, a)
	}
	return eligible, excluded
}
