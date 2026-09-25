package timepin

import (
	"sync"
	"time"
)

// Pinned supplies the "current" unix second used for iat skew and jti
// nonce-window math. Tests pin it via the X-Test-Now-Unix header so
// scenarios are deterministic.
type Pinned struct {
	mu     sync.Mutex
	pinned *int64
}

func New() *Pinned {
	return &Pinned{}
}

func (p *Pinned) NowUnix() int64 {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.pinned != nil {
		return *p.pinned
	}
	return time.Now().Unix()
}

func (p *Pinned) SetUnix(v int64) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.pinned = &v
}
