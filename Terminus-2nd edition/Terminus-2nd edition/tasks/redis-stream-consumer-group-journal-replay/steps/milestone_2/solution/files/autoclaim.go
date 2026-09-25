package claim

import (
	"github.com/terminus/redisstream/internal/staging"
	"github.com/terminus/redisstream/internal/types"
)

func applyXAutoClaim(st *types.StageFile, ev types.JournalEvent) error {
	stream := staging.EnsureStream(st, ev.Stream)
	grp := staging.EnsureGroup(stream, ev.Group)
	now := ev.TimestampMS
	reclaimed := 0
	for id, pel := range grp.Pending {
		if pel.Consumer == ev.Consumer {
			continue
		}
		idle := now - pel.IdleMS
		if idle >= ev.MinIdleMS {
			pel.Consumer = ev.Consumer
			pel.DeliveryCount++
			pel.IdleMS = now
			grp.Pending[id] = pel
			grp.ReclaimTotal++
			reclaimed++
			if ev.Count > 0 && reclaimed >= ev.Count {
				break
			}
		}
	}
	return nil
}
