package sequence

type Tracker struct {
	lastSeq int
}

func NewTracker() *Tracker {
	return &Tracker{}
}

func (t *Tracker) Observe(seq int, isRekeyBoundary bool) bool {
	if seq <= t.lastSeq {
		return false
	}
	t.lastSeq = seq
	return true
}
