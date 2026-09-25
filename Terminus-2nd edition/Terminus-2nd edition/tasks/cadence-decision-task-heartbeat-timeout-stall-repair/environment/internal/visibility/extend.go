package visibility

import "github.com/terminus/cadence-replay/internal/model"

// ExtendOnly bumps visibility deadline without updating progress_seq.
func ExtendOnly(state *model.RuntimeState, atMs int64) {
	state.VisibilityDeadlineMs = atMs + state.Scenario.VisibilityTimeoutMs
}

// SnapshotDeadline exposes the current visibility deadline for diagnostics.
func SnapshotDeadline(state *model.RuntimeState) int64 {
	return state.VisibilityDeadlineMs
}
