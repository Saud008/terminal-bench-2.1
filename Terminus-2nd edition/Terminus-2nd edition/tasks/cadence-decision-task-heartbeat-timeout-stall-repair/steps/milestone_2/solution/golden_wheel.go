package timeout

import "github.com/terminus/cadence-replay/internal/model"

func CheckTimeout(state *model.RuntimeState, nowMs int64) {
	if state.TimedOut {
		return
	}
	sc := state.Scenario
	if state.VisibilityDeadlineMs > 0 && nowMs <= state.VisibilityDeadlineMs {
		return
	}
	if state.LastHeartbeatMs > 0 && nowMs-state.LastHeartbeatMs <= sc.HeartbeatGraceMs {
		return
	}
	if nowMs >= sc.TaskStartMs+sc.StartToCloseTimeoutMs {
		state.TimedOut = true
	}
}
