package party

import (
	"github.com/terminus/party-invite/internal/audit"
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/store"
)

// AuditSnapshotPath is the staging ledger every lifecycle mutation appends to.
const AuditSnapshotPath = audit.LedgerPath

// LoadPartyState reads the live staged state of one party.
// Contract: /app/docs/audit-snapshot.md
func LoadPartyState(st *store.Store, partyID string) (audit.PartyState, bool, error) {
	meta, ok, err := st.PartyMetaFor(partyID)
	if err != nil {
		return audit.PartyState{}, false, err
	}
	if !ok {
		return audit.PartyState{}, false, nil
	}
	members, err := st.ConnectedMemberIDs(partyID)
	if err != nil {
		return audit.PartyState{}, false, err
	}
	pending, err := st.PendingInviteRefs(partyID)
	if err != nil {
		return audit.PartyState{}, false, err
	}
	return audit.PartyState{
		PartyID:      meta.PartyID,
		LeaderID:     meta.LeaderID,
		Status:       meta.Status,
		MaxMembers:   meta.MaxMembers,
		ConnectedIDs: members,
		Pending:      pending,
	}, true, nil
}

// WriteAuditSnapshot stages one party into the audit ledger after a lifecycle mutation.
// Contract: /app/docs/audit-snapshot.md
func WriteAuditSnapshot(st *store.Store, _ clock.Clock, partyID string, monoMs int64) error {
	state, ok, err := LoadPartyState(st, partyID)
	if err != nil {
		return err
	}
	if !ok {
		return nil
	}
	led, err := audit.Load(audit.LedgerPath)
	if err != nil {
		return err
	}
	if !led.AppendIfChanged(state, monoMs) {
		return nil
	}
	return led.Save(audit.LedgerPath)
}

// MarkSweepEpoch advances and persists the ledger sweep epoch, returning the new epoch.
// Contract: /app/docs/sweep-contract.md
func MarkSweepEpoch() (int, error) {
	led, err := audit.Load(audit.LedgerPath)
	if err != nil {
		return 0, err
	}
	led.SweepEpoch++
	if err := led.Save(audit.LedgerPath); err != nil {
		return 0, err
	}
	return led.SweepEpoch, nil
}

// RefreshSnapshotsAfterSweep re-stages surviving parties and retires vanished ones, returning the
// number of retirement entries appended.
// Contract: /app/docs/sweep-contract.md
func RefreshSnapshotsAfterSweep(st *store.Store, _ clock.Clock, monoMs int64) (int, error) {
	led, err := audit.Load(audit.LedgerPath)
	if err != nil {
		return 0, err
	}
	live, err := st.PartyIDsOrdered()
	if err != nil {
		return 0, err
	}

	changed := false
	liveSet := make(map[string]bool, len(live))
	for _, partyID := range live {
		liveSet[partyID] = true
		state, ok, err := LoadPartyState(st, partyID)
		if err != nil {
			return 0, err
		}
		if !ok {
			continue
		}
		if led.AppendIfChanged(state, monoMs) {
			changed = true
		}
	}

	retired := 0
	for _, partyID := range led.PartyIDsWithHistory() {
		if liveSet[partyID] {
			continue
		}
		prev, ok := led.LatestFor(partyID)
		if !ok || prev.Status == "retired" {
			continue
		}
		state := audit.PartyState{
			PartyID:      partyID,
			LeaderID:     prev.LeaderID,
			Status:       "retired",
			MaxMembers:   prev.MaxMembers,
			ConnectedIDs: []string{},
			Pending:      []audit.InviteRef{},
		}
		if led.AppendIfChanged(state, monoMs) {
			changed = true
			retired++
		}
	}

	if changed {
		if err := led.Save(audit.LedgerPath); err != nil {
			return 0, err
		}
	}
	return retired, nil
}
