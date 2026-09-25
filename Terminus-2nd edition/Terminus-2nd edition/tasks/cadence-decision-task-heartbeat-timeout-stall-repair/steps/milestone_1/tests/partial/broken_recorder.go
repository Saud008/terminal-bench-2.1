package heartbeat

import "github.com/terminus/cadence-replay/internal/model"

func ApplyHeartbeat(state *model.RuntimeState, hb model.Heartbeat) {
	timeout := state.Scenario.VisibilityTimeoutMs
	state.VisibilityDeadlineMs = hb.AtMs + timeout
	if hb.ProgressSeq > state.LastProgressSeq {
		state.LastProgressSeq = hb.ProgressSeq
	}
	state.LastHeartbeatMs = hb.AtMs
}
