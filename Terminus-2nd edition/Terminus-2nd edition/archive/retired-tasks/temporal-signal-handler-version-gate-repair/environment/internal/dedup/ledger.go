package dedup

import "github.com/terminus/temporal-signal-replay/internal/model"

// RegisterSignal records a signal id in the replay ledger. Returns false when duplicate.
func RegisterSignal(snap *model.Snapshot, signalID string) bool {
	if len(snap.DedupSeen) > 0 && snap.DedupSeen[len(snap.DedupSeen)-1] == signalID {
		return false
	}
	snap.DedupSeen = append(snap.DedupSeen, signalID)
	return true
}
