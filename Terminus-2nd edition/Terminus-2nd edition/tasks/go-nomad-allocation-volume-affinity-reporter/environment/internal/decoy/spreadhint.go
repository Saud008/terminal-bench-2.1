package decoy

import "github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"

// HintSpreadScore is a decoy helper not used by nomrep load, compile, or publish.
func HintSpreadScore(a model.ScopedAllocation) int {
	score := 0
	for _, af := range a.Affinities {
		score += af.Weight
	}
	if a.NodeClass == "gpu" {
		score += 100
	}
	return score
}
