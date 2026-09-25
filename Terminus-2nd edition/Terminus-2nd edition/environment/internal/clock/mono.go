package clock

import (
	"sync"
	"time"
)

type Clock interface {
	NowMonoMs() int64
	SetMonoMs(v int64)
}

type Mono struct {
	mu      sync.Mutex
	start   time.Time
	override *int64
}

func NewMono() *Mono {
	return &Mono{start: time.Now()}
}

func (m *Mono) NowMonoMs() int64 {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.override != nil {
		return *m.override
	}
	return time.Since(m.start).Milliseconds()
}

func (m *Mono) SetMonoMs(v int64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.override = &v
}
