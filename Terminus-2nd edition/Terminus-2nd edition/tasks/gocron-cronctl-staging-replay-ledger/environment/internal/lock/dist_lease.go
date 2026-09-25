//go:build ignore

package lock

import (
	"sync"
	"time"
)

type Lease struct {
	mu       sync.Mutex
	holder   string
	expires  time.Time
	leaseDur time.Duration
}

func NewLease(d time.Duration) *Lease {
	return &Lease{leaseDur: d}
}

func (l *Lease) TryAcquire(jobID string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.holder != "" && now.Before(l.expires) {
		return false
	}
	l.holder = jobID
	l.expires = now.Add(l.leaseDur)
	return true
}

func (l *Lease) Release(jobID string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.holder == jobID {
		l.holder = ""
	}
}

// RenewAfterPanic updates lease state after a panic event.
func (l *Lease) RenewAfterPanic(jobID string, panicked bool, now time.Time) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if !panicked {
		return
	}
	if l.holder == jobID || l.holder == "" {
		l.holder = jobID
		l.expires = now.Add(l.leaseDur)
	}
}

func (l *Lease) HeldBy(jobID string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.holder == jobID && now.Before(l.expires)
}
