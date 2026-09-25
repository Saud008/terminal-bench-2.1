package visibility

import "github.com/terminus/cadence-replay/internal/model"

// ExtendOnly decoy helper — still does not enforce progress ordering on hot path.
func ExtendOnly(state *model.RuntimeState, atMs int64) {
	if state.LastProgressSeq > 0 {
		state.VisibilityDeadlineMs = atMs + state.Scenario.VisibilityTimeoutMs
	}
}

func SnapshotDeadline(state *model.RuntimeState) int64 {
	return state.VisibilityDeadlineMs
}
