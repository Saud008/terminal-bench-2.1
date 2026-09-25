package causalorder

import (
	"sort"

	"github.com/terminus/vcreplay/internal/model"
	"github.com/terminus/vcreplay/internal/lamportmesh"
)

func CausalSort(events []model.StagedEvent) []model.StagedEvent {
	out := append([]model.StagedEvent(nil), events...)
	sort.Slice(out, func(i, j int) bool {
		a := out[i]
		b := out[j]
		if lamportmesh.HappensBefore(a.VectorClock, b.VectorClock) {
			return true
		}
		if lamportmesh.HappensBefore(b.VectorClock, a.VectorClock) {
			return false
		}
		return a.EventID < b.EventID
	})
	return out
}
