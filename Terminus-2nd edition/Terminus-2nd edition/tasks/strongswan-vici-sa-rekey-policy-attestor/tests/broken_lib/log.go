package sequence

type Tracker struct {
	lastSeq    int
	rekeyReset bool
}

func NewTracker() *Tracker {
	return &Tracker{}
}

func (t *Tracker) Observe(seq int, isRekeyBoundary bool) bool {
	if isRekeyBoundary {
		t.rekeyReset = true
		t.lastSeq = seq
		return true
	}
	if t.rekeyReset {
		t.rekeyReset = false
		if seq <= t.lastSeq {
			return false
		}
	}
	if seq <= t.lastSeq {
		return false
	}
	t.lastSeq = seq
	return true
}
