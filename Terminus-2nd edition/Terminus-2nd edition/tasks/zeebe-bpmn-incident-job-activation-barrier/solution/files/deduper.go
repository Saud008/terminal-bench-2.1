package replay

import "github.com/terminus/actplay/internal/model"

func ShouldActivate(snap *model.Snapshot, batch model.ReplayBatch, jobKey string) bool {
	pair := batch.BatchID + ":" + jobKey
	if !batch.Idempotent {
		return true
	}
	for _, seen := range snap.DedupPairs {
		if seen == pair {
			return false
		}
	}
	return true
}

func RecordActivation(snap *model.Snapshot, batch model.ReplayBatch, jobKey string) {
	pair := batch.BatchID + ":" + jobKey
	snap.DedupPairs = append(snap.DedupPairs, pair)
}
