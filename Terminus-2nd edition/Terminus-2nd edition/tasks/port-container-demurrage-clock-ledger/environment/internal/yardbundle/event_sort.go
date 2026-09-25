package yardbundle

import "github.com/terminus/demurctl/internal/model"

// SortGateEvents orders gate events for dwell pairing.
func SortGateEvents(events []model.GateEvent) []model.GateEvent {
	out := make([]model.GateEvent, len(events))
	copy(out, events)
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[i].Ts < out[j].Ts {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out
}
