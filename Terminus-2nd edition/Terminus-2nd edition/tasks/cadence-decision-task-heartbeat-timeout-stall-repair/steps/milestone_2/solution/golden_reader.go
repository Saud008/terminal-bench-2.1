package history

import "github.com/terminus/cadence-replay/internal/model"

func ApplyEvent(state *model.RuntimeState, ev model.HistoryEvent) {
	if state.SeenEventIDs[ev.EventID] {
		state.DuplicateSkipped++
		return
	}
	state.SeenEventIDs[ev.EventID] = true
	state.AppliedNames = append(state.AppliedNames, ev.Name)
	if ev.Seq > state.HistoryCursorSeq {
		state.HistoryCursorSeq = ev.Seq
	}
}
