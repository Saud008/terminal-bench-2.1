package replay

import "github.com/terminus/pulsar-dedup-replay/internal/model"

// NoteReplay increments counters when the same msg_id is seen again.
func NoteReplay(st *model.StreamStats) {
	st.DedupMiss++
}
