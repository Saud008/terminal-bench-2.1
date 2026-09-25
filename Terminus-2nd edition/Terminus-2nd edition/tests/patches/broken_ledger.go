package audit

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sort"
)

// LedgerPath is the on-disk audit staging ledger.
// Contract: /app/docs/audit-snapshot.md
const LedgerPath = "/app/state/party-audit-snapshot.json"

// SnapshotVersion is the only ledger schema version export accepts.
const SnapshotVersion = 2

// RetainedEntries is the size of the retained entry window.
const RetainedEntries = 8

// Entry is one appended staging record.
type Entry struct {
	Seq          int         `json:"seq"`
	PartySeq     int         `json:"party_seq"`
	PartyID      string      `json:"party_id"`
	LeaderID     string      `json:"leader_id"`
	Status       string      `json:"status"`
	MaxMembers   int         `json:"max_members"`
	StagedMonoMs int64       `json:"staged_mono_ms"`
	SweepEpoch   int         `json:"sweep_epoch"`
	ConnectedIDs []string    `json:"connected_ids"`
	Pending      []InviteRef `json:"pending_invites"`
	PrevDigest   string      `json:"prev_digest"`
	EntryDigest  string      `json:"entry_digest"`
}

// Ledger is the append-only staging chain.
type Ledger struct {
	SnapshotVersion int            `json:"snapshot_version"`
	AuditSeq        int            `json:"audit_seq"`
	SweepEpoch      int            `json:"sweep_epoch"`
	ChainBase       string         `json:"chain_base"`
	ChainHead       string         `json:"chain_head"`
	PartySeqs       map[string]int `json:"party_seqs"`
	Entries         []Entry        `json:"entries"`
}

// NewLedger returns an empty ledger chaining from Genesis.
func NewLedger() *Ledger {
	return &Ledger{
		SnapshotVersion: SnapshotVersion,
		ChainBase:       Genesis,
		ChainHead:       Genesis,
		PartySeqs:       map[string]int{},
		Entries:         []Entry{},
	}
}

// Load reads the ledger, returning an empty one when the file does not exist yet.
func Load(path string) (*Ledger, error) {
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return NewLedger(), nil
	}
	if err != nil {
		return nil, err
	}
	var led Ledger
	if err := json.Unmarshal(raw, &led); err != nil {
		return nil, err
	}
	if led.PartySeqs == nil {
		led.PartySeqs = map[string]int{}
	}
	if led.Entries == nil {
		led.Entries = []Entry{}
	}
	return &led, nil
}

// Save writes the ledger back, normalising empty lists.
func (l *Ledger) Save(path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	for i := range l.Entries {
		if l.Entries[i].ConnectedIDs == nil {
			l.Entries[i].ConnectedIDs = []string{}
		}
		if l.Entries[i].Pending == nil {
			l.Entries[i].Pending = []InviteRef{}
		}
	}
	if l.PartySeqs == nil {
		l.PartySeqs = map[string]int{}
	}
	raw, err := json.MarshalIndent(l, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

// LatestFor returns the newest retained entry of one party.
func (l *Ledger) LatestFor(partyID string) (Entry, bool) {
	for i := len(l.Entries) - 1; i >= 0; i-- {
		if l.Entries[i].PartyID == partyID {
			return l.Entries[i], true
		}
	}
	return Entry{}, false
}

// PartyIDsWithHistory lists every party the ledger ever staged, ascending.
func (l *Ledger) PartyIDsWithHistory() []string {
	out := make([]string, 0, len(l.PartySeqs))
	for partyID := range l.PartySeqs {
		out = append(out, partyID)
	}
	sort.Strings(out)
	return out
}

// AppendIfChanged appends one entry unless suppression applies, reporting whether the ledger
// changed. Implement per /app/docs/audit-snapshot.md.
func (l *Ledger) AppendIfChanged(st PartyState, stagedMonoMs int64) bool {
	_ = st
	_ = stagedMonoMs
	return false
}

// Verify checks the retained chain before export publishes.
// Implement per /app/docs/audit-snapshot.md.
func (l *Ledger) Verify() error {
	return nil
}
