package sequence

import "github.com/terminus/pulsar-dedup-replay/internal/model"

func ApplyLocalSequence(snap *model.Snapshot, key string, seq int64) {
	st := snap.Streams[key]
	if seq > st.HighWater {
		st.HighWater = seq
		st.BrokerAckedMax = seq
	}
	snap.Streams[key] = st
}
