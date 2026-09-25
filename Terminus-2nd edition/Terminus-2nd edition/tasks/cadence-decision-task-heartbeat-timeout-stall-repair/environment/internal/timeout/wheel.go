package timeout

import "github.com/terminus/cadence-replay/internal/model"

// CheckTimeout evaluates whether the decision task should time out at nowMs.
func CheckTimeout(state *model.RuntimeState, nowMs int64) {
	if state.TimedOut {
		return
	}
	sc := state.Scenario
	if nowMs >= sc.TaskStartMs+sc.StartToCloseTimeoutMs {
		state.TimedOut = true
	}
}
