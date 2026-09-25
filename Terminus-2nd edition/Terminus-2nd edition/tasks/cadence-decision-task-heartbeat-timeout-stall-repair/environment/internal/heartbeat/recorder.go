package heartbeat

import "github.com/terminus/cadence-replay/internal/model"

// ApplyHeartbeat records worker progress and extends decision-task visibility.
func ApplyHeartbeat(state *model.RuntimeState, hb model.Heartbeat) {
	timeout := state.Scenario.VisibilityTimeoutMs
	state.VisibilityDeadlineMs = hb.AtMs + timeout
	if hb.ProgressSeq > state.LastProgressSeq {
		state.LastProgressSeq = hb.ProgressSeq
	}
	state.LastHeartbeatMs = hb.AtMs
}
