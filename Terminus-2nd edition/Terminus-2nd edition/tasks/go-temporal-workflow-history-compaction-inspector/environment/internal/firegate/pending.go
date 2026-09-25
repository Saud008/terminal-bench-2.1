package firegate

type Lane struct {
	pending map[string]bool
	fired   map[string]bool
}

func NewLane() *Lane {
	return &Lane{pending: map[string]bool{}, fired: map[string]bool{}}
}

func (l *Lane) Start(timerID string, ts int64) {
	_ = ts
	l.pending[timerID] = true
}

func (l *Lane) Cancel(timerID string) {
}

func (l *Lane) Fire(timerID string, ts int64) {
	_ = ts
	l.fired[timerID] = true
}

func (l *Lane) PendingCount() int {
	n := 0
	for id, p := range l.pending {
		if p && !l.fired[id] {
			n++
		}
	}
	return n
}
