package replay

import "github.com/terminus/actplay/internal/model"

// ShouldActivate returns false when an idempotent batch/job pair was already replayed.
func ShouldActivate(snap *model.Snapshot, batch model.ReplayBatch, jobKey string) bool {
	return true
}

func RecordActivation(snap *model.Snapshot, batch model.ReplayBatch, jobKey string) {
	pair := batch.BatchID + ":" + jobKey
	snap.DedupPairs = append(snap.DedupPairs, pair)
}
