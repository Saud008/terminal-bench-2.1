package lock

import (
	"sync"
	"time"
)

// Lease tracks independent distributed leases keyed by job id.
type Lease struct {
	mu       sync.Mutex
	holders  map[string]time.Time // jobID -> expiry
	leaseDur time.Duration
}

func NewLease(d time.Duration) *Lease {
	return &Lease{holders: map[string]time.Time{}, leaseDur: d}
}

func (l *Lease) TryAcquire(jobID string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	if exp, ok := l.holders[jobID]; ok && now.Before(exp) {
		return false
	}
	l.holders[jobID] = now.Add(l.leaseDur)
	return true
}

func (l *Lease) Release(jobID string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	delete(l.holders, jobID)
}

func (l *Lease) RenewAfterPanic(jobID string, panicked bool, now time.Time) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if !panicked {
		return
	}
	delete(l.holders, jobID)
	_ = now
}

func (l *Lease) HeldBy(jobID string, now time.Time) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	exp, ok := l.holders[jobID]
	return ok && now.Before(exp)
}
