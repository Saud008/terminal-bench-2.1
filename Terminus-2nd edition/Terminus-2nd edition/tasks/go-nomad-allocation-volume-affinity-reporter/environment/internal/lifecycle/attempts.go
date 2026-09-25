package lifecycle

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

func RescheduleTotal(allocs []model.ScopedAllocation) int {
	total := 0
	for _, a := range allocs {
		if a.RescheduleAttempts > 0 {
			total += a.RescheduleAttempts
		}
	}
	return total
}
