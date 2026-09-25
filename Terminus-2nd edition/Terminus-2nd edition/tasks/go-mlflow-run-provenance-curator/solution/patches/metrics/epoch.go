package metrics

import (
	"sort"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

func OrderMetrics(points []model.MetricPoint) []model.MetricPoint {
	out := append([]model.MetricPoint(nil), points...)
	sort.Slice(out, func(i, j int) bool {
		if out[i].Epoch != out[j].Epoch {
			return out[i].Epoch < out[j].Epoch
		}
		if out[i].Step != out[j].Step {
			return out[i].Step < out[j].Step
		}
		return out[i].Key < out[j].Key
	})
	return out
}

func EpochMonotonicOK(ordered []model.MetricPoint) bool {
	if len(ordered) == 0 {
		return true
	}
	maxStepInEpoch := map[int]int{}
	prevEpoch := ordered[0].Epoch
	maxStepInEpoch[prevEpoch] = ordered[0].Step
	for i := 1; i < len(ordered); i++ {
		m := ordered[i]
		if m.Epoch > prevEpoch {
			prevMax := maxStepInEpoch[prevEpoch]
			if m.Step < prevMax {
				return false
			}
			prevEpoch = m.Epoch
		}
		if m.Step > maxStepInEpoch[m.Epoch] {
			maxStepInEpoch[m.Epoch] = m.Step
		}
	}
	return true
}
