// Package chainhead stages /app/state/chainhead.json after every
// admit/deny decision. See /app/docs/chainhead-stage.md for the required
// schema and head-chaining formula.
package chainhead

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/jktadmit-gate/internal/schema"
)

const SnapshotPath = "/app/state/chainhead.json"

type Snapshot struct {
	Version       int                  `json:"version"`
	Principal     string               `json:"principal"`
	Session       string               `json:"session"`
	JKT           string               `json:"jkt"`
	ChainSeq      int                  `json:"chain_seq"`
	ChainHead     string               `json:"chain_head"`
	AdmittedTotal int                  `json:"admitted_total"`
	DeniedTotal   int                  `json:"denied_total"`
	DenyTotals    map[string]int       `json:"deny_totals"`
	ChainEvents   []schema.ChainEvent  `json:"chain_events"`
}

// ComputeHead implements the chain_head formula from
// /app/docs/chainhead-stage.md.
func ComputeHead(prevHead, principal, session string, seq int, verdictToken string) string {
	msg := fmt.Sprintf("%s:%s:%s:%d:%s", prevHead, principal, session, seq, verdictToken)
	sum := sha256.Sum256([]byte(msg))
	return hex.EncodeToString(sum[:])
}

func ReadSnapshot() (Snapshot, error) {
	raw, err := os.ReadFile(SnapshotPath)
	if err != nil {
		return Snapshot{}, err
	}
	var snap Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return Snapshot{}, err
	}
	return snap, nil
}

func writeSnapshotFile(snap Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(SnapshotPath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(SnapshotPath, append(raw, '\n'), 0o644)
}

func verdictToken(events []schema.ChainEvent) string {
	if len(events) == 0 {
		return "none"
	}
	last := events[len(events)-1]
	if last.Verdict == "admit" {
		return "admit:" + last.Jti
	}
	return "deny:" + last.Reason
}

// Stage computes the next chain_head for sess (chaining off the previous
// on-disk snapshot for this principal/session, if any) and writes the
// snapshot file. It returns the session with ChainHead populated so the
// caller can persist it back to the store.
//
// Shipping calibration: reorders chain_events by jti string before
// writing, corrupting the ascending chain_seq order that
// /app/docs/chainhead-stage.md requires chain_events to preserve.
func Stage(sess schema.SessionState) (schema.SessionState, error) {
	prevHead := ""
	if prev, err := ReadSnapshot(); err == nil && prev.Principal == sess.Principal && prev.Session == sess.Session {
		prevHead = prev.ChainHead
	}
	sess.ChainHead = ComputeHead(prevHead, sess.Principal, sess.Session, sess.ChainSeq, verdictToken(sess.ChainEvents))

	events := make([]schema.ChainEvent, len(sess.ChainEvents))
	copy(events, sess.ChainEvents)
	sort.Slice(events, func(i, j int) bool { return events[i].Jti < events[j].Jti })

	snap := Snapshot{
		Version:       1,
		Principal:     sess.Principal,
		Session:       sess.Session,
		JKT:           sess.JKT,
		ChainSeq:      sess.ChainSeq,
		ChainHead:     sess.ChainHead,
		AdmittedTotal: sess.AdmittedTotal,
		DeniedTotal:   sess.DeniedTotal,
		DenyTotals:    sess.DenyTotals,
		ChainEvents:   events,
	}
	if err := writeSnapshotFile(snap); err != nil {
		return sess, fmt.Errorf("chainhead stage: %w", err)
	}
	return sess, nil
}
