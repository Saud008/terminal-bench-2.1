package replay

import "github.com/terminus/pulsar-dedup-replay/internal/model"

func NoteReplay(st *model.StreamStats) {
	st.DedupMiss++
}
