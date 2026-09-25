package retention

import (
	"github.com/terminus/asynq-archive-repair/internal/clock"
	"github.com/terminus/asynq-archive-repair/internal/queue"
)

func PurgeBefore(store *queue.Store, beforeRFC3339 string, skewMs int64) (int64, error) {
	cutoff, err := clock.ParseRFC3339UTC(beforeRFC3339)
	if err != nil {
		return 0, err
	}
	cutoffMs := clock.MsUTC(cutoff) + skewMs + 60000
	return store.PurgeArchivedBefore(cutoffMs)
}
