package history

import "github.com/terminus/cadence-replay/internal/model"

// ApplyEvent merges a history event into replay state.
func ApplyEvent(state *model.RuntimeState, ev model.HistoryEvent) {
	if state.SeenEventIDs[ev.EventID] {
		state.DuplicateSkipped++
		state.HistoryCursorSeq = ev.EventID
		return
	}
	state.SeenEventIDs[ev.EventID] = true
	state.AppliedNames = append(state.AppliedNames, ev.Name)
	state.HistoryCursorSeq = ev.EventID
}
