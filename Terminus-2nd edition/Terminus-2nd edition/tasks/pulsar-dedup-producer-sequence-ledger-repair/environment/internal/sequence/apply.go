package sequence

import "github.com/terminus/pulsar-dedup-replay/internal/model"

// ApplyLocalSequence updates high water on the snapshot stream stats directly.
func ApplyLocalSequence(snap *model.Snapshot, key string, seq int64) {
	st := snap.Streams[key]
	if seq > st.HighWater {
		st.HighWater = seq
	}
	snap.Streams[key] = st
}
