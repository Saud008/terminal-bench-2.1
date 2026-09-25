package party

import (
	"errors"
	"os"

	"github.com/terminus/party-invite/internal/audit"
	"github.com/terminus/party-invite/internal/model"
)

// BuildAuditReport publishes the checkpoint-backed occupancy report from the verified ledger.
// Contract: /app/docs/export-schema.md
func BuildAuditReport(d *DAO, partyID string, monoMs int64) (model.AuditReport, error) {
	if _, err := os.Stat(audit.LedgerPath); err != nil {
		return model.AuditReport{}, errors.New("audit ledger unavailable")
	}
	led, err := audit.Load(audit.LedgerPath)
	if err != nil || led.SnapshotVersion != audit.SnapshotVersion {
		return model.AuditReport{}, errors.New("audit ledger unavailable")
	}
	if err := led.Verify(); err != nil {
		return model.AuditReport{}, errors.New("audit ledger chain broken")
	}
	entry, ok := led.LatestFor(partyID)
	if !ok {
		return model.AuditReport{}, errors.New("audit ledger party unstaged")
	}
	if entry.Status == "retired" {
		return model.AuditReport{}, errors.New("audit ledger party retired")
	}
	meta, ok, err := d.Store.PartyMetaFor(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	if !ok {
		return model.AuditReport{}, errors.New("audit ledger party missing")
	}
	if meta.Status != entry.Status || meta.LeaderID != entry.LeaderID || meta.MaxMembers != entry.MaxMembers {
		return model.AuditReport{}, errors.New("audit ledger drift")
	}

	connectedIDs, err := d.Store.ConnectedMemberIDs(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	joined := make(map[string]bool, len(connectedIDs))
	for _, playerID := range connectedIDs {
		joined[playerID] = true
	}

	reservedFor := map[string]bool{}
	stale := 0
	for _, ref := range entry.Pending {
		if ref.ExpiresMs <= monoMs {
			stale++
			continue
		}
		if joined[ref.InviteeID] {
			continue
		}
		reservedFor[ref.InviteeID] = true
	}
	reserved := len(reservedFor)

	pending, err := d.Store.CountPendingInvites(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	expiredPending, err := d.Store.CountExpiredPendingInvites(partyID, monoMs)
	if err != nil {
		return model.AuditReport{}, err
	}
	leaderOK, err := d.Store.LeaderConnected(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}

	return model.AuditReport{
		PartyID:               entry.PartyID,
		LeaderID:              entry.LeaderID,
		Status:                entry.Status,
		MaxMembers:            entry.MaxMembers,
		ConnectedMembers:      len(connectedIDs),
		PendingInvites:        pending,
		EffectiveOccupancy:    len(connectedIDs) + reserved,
		ExpiredPendingInvites: expiredPending,
		OrphanParty:           entry.Status == "active" && !leaderOK,
		AuditSeq:              led.AuditSeq,
		StagedPartySeq:        entry.PartySeq,
		SweepEpoch:            led.SweepEpoch,
		ChainHead:             led.ChainHead,
		ReservedSlots:         reserved,
		StaleStagedInvites:    stale,
	}, nil
}
