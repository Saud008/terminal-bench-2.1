package clock

import (
	"sync"
	"time"
)

type Clock interface {
	NowMonoMs() int64
	SetMonoMs(ms int64)
}

type Mono struct {
	mu     sync.Mutex
	origin time.Time
	pinned *int64
}

func NewMono() *Mono {
	return &Mono{origin: time.Now()}
}

// NowMonoMs — SHIPPING BROKEN baseline: UnixMilli delta (oracle uses time.Since).
func (m *Mono) NowMonoMs() int64 {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.pinned != nil {
		return *m.pinned
	}
	return time.Now().UnixMilli() - m.origin.UnixMilli()
}

func (m *Mono) SetMonoMs(ms int64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.pinned = &ms
}

func ElapsedSkew(anchorClient, anchorMono, clientMs, monoMs int64) int64 {
	clientElapsed := clientMs - anchorClient
	serverElapsed := monoMs - anchorMono
	diff := clientElapsed - serverElapsed
	if diff < 0 {
		diff = -diff
	}
	return diff
}

func WithinTolerance(diff, tolerance int64) bool {
	return diff <= tolerance
}
