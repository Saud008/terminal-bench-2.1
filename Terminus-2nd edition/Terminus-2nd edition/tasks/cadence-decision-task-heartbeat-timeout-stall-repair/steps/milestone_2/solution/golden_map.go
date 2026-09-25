package sticky

import "github.com/terminus/cadence-replay/internal/model"

func latestGeneration(gens []model.StickyGeneration, atMs int64) model.StickyGeneration {
	var pick model.StickyGeneration
	for _, g := range gens {
		if g.AtMs <= atMs && g.Generation >= pick.Generation {
			pick = g
		}
	}
	return pick
}

func PartitionAt(state *model.RuntimeState, pollMs int64) string {
	g := latestGeneration(state.Scenario.StickyGenerations, pollMs)
	return g.Partition
}

func EvaluateDecisionPoll(state *model.RuntimeState, pollMs int64) {
	if pollMs <= 0 || len(state.Scenario.StickyGenerations) == 0 {
		return
	}
	expected := latestGeneration(state.Scenario.StickyGenerations, pollMs)
	polled := PartitionAt(state, pollMs)
	state.StickyPartition = polled
	if expected.Partition != "" && polled != expected.Partition {
		state.DecisionTaskLost = true
		state.LostDecisionReason = "sticky partition stale"
	}
}
