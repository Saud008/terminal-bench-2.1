package batch

import "github.com/terminus/pulsar-dedup-replay/internal/model"

func AdvanceBatchHighWater(snap *model.Snapshot, key string, seqs []int64) {
	st := snap.Streams[key]
	for _, seq := range seqs {
		if seq > st.HighWater {
			st.HighWater = seq
		}
	}
	snap.Streams[key] = st
}
