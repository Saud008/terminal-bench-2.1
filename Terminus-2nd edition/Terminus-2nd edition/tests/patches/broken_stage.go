package party

import (
	"github.com/terminus/party-invite/internal/audit"
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/store"
)

// AuditSnapshotPath is the staging ledger every lifecycle mutation appends to.
const AuditSnapshotPath = audit.LedgerPath

// LoadPartyState reads the live staged state of one party.
// Implement per /app/docs/audit-snapshot.md.
func LoadPartyState(st *store.Store, partyID string) (audit.PartyState, bool, error) {
	_ = st
	_ = partyID
	return audit.PartyState{}, false, nil
}

// WriteAuditSnapshot stages one party into the audit ledger after a lifecycle mutation.
// Implement per /app/docs/audit-snapshot.md.
func WriteAuditSnapshot(st *store.Store, _ clock.Clock, partyID string, monoMs int64) error {
	_ = st
	_ = partyID
	_ = monoMs
	return nil
}

// MarkSweepEpoch advances and persists the ledger sweep epoch, returning the new epoch.
// Implement per /app/docs/sweep-contract.md.
func MarkSweepEpoch() (int, error) {
	return 0, nil
}

// RefreshSnapshotsAfterSweep re-stages surviving parties and retires vanished ones, returning the
// number of retirement entries appended.
// Implement per /app/docs/sweep-contract.md.
func RefreshSnapshotsAfterSweep(st *store.Store, clk clock.Clock, monoMs int64) (int, error) {
	_ = st
	_ = clk
	_ = monoMs
	return 0, nil
}
