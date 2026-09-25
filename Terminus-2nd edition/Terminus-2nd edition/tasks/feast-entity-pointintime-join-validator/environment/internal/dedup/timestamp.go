package dedup

import (
	"sort"

	"github.com/terminus/feast-pit-join/internal/model"
)

func DeduplicateEvents(events []model.MaterializedEvent) ([]model.MaterializedEvent, int) {
	type key struct {
		entity, device, session, feature, source string
		ts                                       int64
	}
	best := map[key]model.MaterializedEvent{}
	for _, ev := range events {
		k := key{ev.EntityID, ev.DeviceID, ev.SessionID, ev.Feature, ev.Source, ev.EventTS}
		if cur, ok := best[k]; !ok || ev.Seq < cur.Seq {
			best[k] = ev
		}
	}
	out := make([]model.MaterializedEvent, 0, len(best))
	for _, v := range best {
		out = append(out, v)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].EventTS != out[j].EventTS {
			return out[i].EventTS < out[j].EventTS
		}
		return out[i].EntityID < out[j].EntityID
	})
	return out, len(events) - len(out)
}
