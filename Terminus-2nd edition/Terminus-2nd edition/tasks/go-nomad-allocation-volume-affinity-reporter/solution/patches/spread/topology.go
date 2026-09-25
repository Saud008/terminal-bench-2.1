package spread

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

const penaltyWeight = 10

func PenaltyFor(a model.ScopedAllocation, peers []model.ScopedAllocation) int {
	count := 0
	for _, o := range peers {
		if o.NodeID == a.NodeID && o.AllocID != a.AllocID {
			count++
		}
	}
	return count * penaltyWeight
}

func PenaltyTotal(allocs []model.ScopedAllocation) int {
	total := 0
	for _, a := range allocs {
		total += PenaltyFor(a, allocs)
	}
	return total
}

func AdjustScore(base int, a model.ScopedAllocation, peers []model.ScopedAllocation) int {
	return base - PenaltyFor(a, peers)
}
