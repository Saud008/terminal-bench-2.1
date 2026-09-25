// Package jtiledger tracks jti consumption per pinned jkt so a captured
// proof cannot be re-submitted. See /app/docs/jti-nonce-window.md for the
// required membership and window semantics.
package jtiledger

import "sync"

type entry struct {
	expiresAtUnix int64
}

type Ledger struct {
	mu   sync.Mutex
	seen map[string]entry
}

func NewLedger() *Ledger {
	return &Ledger{seen: make(map[string]entry)}
}

// CheckAndRecord reports whether (jkt, jti) is a replay and records the
// presentation for future window checks. Membership is checked BEFORE the
// new presentation is recorded, per /app/docs/jti-nonce-window.md.
func (l *Ledger) CheckAndRecord(jkt, jti string, nowUnix, windowSec int64) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	key := jkt + ":" + jti
	if prev, ok := l.seen[key]; ok && prev.expiresAtUnix >= nowUnix {
		return true
	}
	l.seen[key] = entry{expiresAtUnix: nowUnix + windowSec}
	return false
}

func (l *Ledger) Reset() {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.seen = make(map[string]entry)
}
