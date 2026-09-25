package batch

import "github.com/terminus/pulsar-dedup-replay/internal/model"

func AdvanceBatchHighWater(snap *model.Snapshot, key string, seqs []int64) {
	_ = snap
	_ = key
	_ = seqs
}
