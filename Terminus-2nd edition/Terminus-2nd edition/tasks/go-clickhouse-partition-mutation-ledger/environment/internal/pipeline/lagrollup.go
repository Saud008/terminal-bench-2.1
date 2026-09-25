package pipeline

import (
	"github.com/terminus/chmutled/internal/model"
	"github.com/terminus/chmutled/internal/replag"
)

func lagMap(reps []model.ReplicaLog) map[string]int {
	m := map[string][]int{}
	for _, r := range reps {
		m[r.PartitionID] = append(m[r.PartitionID], r.LagSec)
	}
	out := map[string]int{}
	for pid, lags := range m {
		out[pid] = replag.MaxLag(lags)
	}
	return out
}
