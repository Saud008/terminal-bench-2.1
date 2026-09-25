package dedup

import "github.com/terminus/temporal-signal-replay/internal/model"

func RegisterSignal(snap *model.Snapshot, signalID string) bool {
	for _, id := range snap.DedupSeen {
		if id == signalID {
			return false
		}
	}
	snap.DedupSeen = append(snap.DedupSeen, signalID)
	return true
}
