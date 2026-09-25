package heartbeat

import "github.com/terminus/cadence-replay/internal/model"

func ApplyHeartbeat(state *model.RuntimeState, hb model.Heartbeat) {
	timeout := state.Scenario.VisibilityTimeoutMs
	if hb.ProgressSeq > state.LastProgressSeq {
		state.LastProgressSeq = hb.ProgressSeq
		state.VisibilityDeadlineMs = hb.AtMs + timeout
		state.LastHeartbeatMs = hb.AtMs
		return
	}
	if hb.ProgressSeq == state.LastProgressSeq {
		state.VisibilityDeadlineMs = hb.AtMs + timeout
		state.LastHeartbeatMs = hb.AtMs
	}
}
