package party

import (
	"github.com/terminus/party-invite/internal/model"
)

// BuildAuditReport publishes the checkpoint-backed occupancy report.
// Implement per /app/docs/export-schema.md: verify the audit staging ledger, refuse with the
// documented token when a check fails, and seal occupancy from the staged entry.
func BuildAuditReport(d *DAO, partyID string, monoMs int64) (model.AuditReport, error) {
	return d.buildAuditFromDB(partyID, monoMs)
}

// buildAuditFromDB is the pre-ledger export path: it re-walks SQLite invite rows for occupancy and
// ignores the staging ledger entirely.
func (d *DAO) buildAuditFromDB(partyID string, monoMs int64) (model.AuditReport, error) {
	party, err := d.GetParty(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	connected, err := d.Store.CountConnectedMembers(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	pending, err := d.Store.CountPendingInvites(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	expiredPending, err := d.Store.CountExpiredPendingInvites(partyID, monoMs)
	if err != nil {
		return model.AuditReport{}, err
	}
	effective := connected + pending - expiredPending
	if effective < connected {
		effective = connected
	}
	leaderOK, err := d.Store.LeaderConnected(partyID)
	if err != nil {
		return model.AuditReport{}, err
	}
	orphan := party.Status == "active" && !leaderOK
	return model.AuditReport{
		PartyID:               partyID,
		LeaderID:              party.LeaderID,
		Status:                party.Status,
		MaxMembers:            party.MaxMembers,
		ConnectedMembers:      connected,
		PendingInvites:        pending,
		EffectiveOccupancy:    effective,
		ExpiredPendingInvites: expiredPending,
		OrphanParty:           orphan,
	}, nil
}
