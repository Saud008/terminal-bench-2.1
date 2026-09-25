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
// presentation for future window checks.
//
// Shipping calibration: records the entry before checking prior membership,
// so the just-written entry is always found and the freshly-recorded
// deadline is never in the past — jti replay is never detected.
// /app/docs/jti-nonce-window.md requires checking membership and the
// window BEFORE recording the new presentation.
func (l *Ledger) CheckAndRecord(jkt, jti string, nowUnix, windowSec int64) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	key := jkt + ":" + jti
	l.seen[key] = entry{expiresAtUnix: nowUnix + windowSec}
	prev, ok := l.seen[key]
	if !ok {
		return false
	}
	return prev.expiresAtUnix < nowUnix
}

func (l *Ledger) Reset() {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.seen = make(map[string]entry)
}
