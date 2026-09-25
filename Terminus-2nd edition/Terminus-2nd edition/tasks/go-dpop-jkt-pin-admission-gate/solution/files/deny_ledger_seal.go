// Package auditseal publishes the digest-sealed deny ledger to
// /app/output/deny-ledger.json. See /app/docs/deny-ledger-seal.md for the
// required schema and merge rule.
package auditseal

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/jktadmit-gate/internal/chainhead"
)

const LedgerPath = "/app/output/deny-ledger.json"

type Ledger struct {
	Principal     string         `json:"principal"`
	Session       string         `json:"session"`
	JKT           string         `json:"jkt"`
	AdmittedTotal int            `json:"admitted_total"`
	DeniedTotal   int            `json:"denied_total"`
	DenyTotals    map[string]int `json:"deny_totals"`
	ChainSeq      int            `json:"chain_seq"`
	ChainHead     string         `json:"chain_head"`
	SealDigest    string         `json:"seal_digest"`
}

type Publisher struct{}

// Build reads the chainhead snapshot for (principal, session) and seals it
// into the ledger contract, copying every counter unchanged per
// /app/docs/deny-ledger-seal.md. No operational/debug field is added.
func (p *Publisher) Build(principal, session string) (Ledger, error) {
	snap, err := chainhead.ReadSnapshot()
	if err != nil {
		return Ledger{}, fmt.Errorf("chainhead snapshot required")
	}
	if snap.Principal != principal || snap.Session != session {
		return Ledger{}, fmt.Errorf("chainhead snapshot mismatch")
	}
	deny := make(map[string]int, len(snap.DenyTotals))
	for k, v := range snap.DenyTotals {
		deny[k] = v
	}

	ledger := Ledger{
		Principal:     principal,
		Session:       session,
		JKT:           snap.JKT,
		AdmittedTotal: snap.AdmittedTotal,
		DeniedTotal:   snap.DeniedTotal,
		DenyTotals:    deny,
		ChainSeq:      snap.ChainSeq,
		ChainHead:     snap.ChainHead,
	}
	ledger.SealDigest = SealDigest(ledger)
	return ledger, nil
}

func (p *Publisher) Write(path string, ledger Ledger) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

// SealDigest hashes the canonical compact JSON encoding of every ledger
// field except seal_digest, with object keys sorted lexicographically.
func SealDigest(l Ledger) string {
	m := map[string]any{
		"principal":      l.Principal,
		"session":        l.Session,
		"jkt":            l.JKT,
		"admitted_total": l.AdmittedTotal,
		"denied_total":   l.DeniedTotal,
		"deny_totals":    l.DenyTotals,
		"chain_seq":      l.ChainSeq,
		"chain_head":     l.ChainHead,
	}
	raw, err := json.Marshal(m)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(raw)
	return hex.EncodeToString(sum[:])
}
