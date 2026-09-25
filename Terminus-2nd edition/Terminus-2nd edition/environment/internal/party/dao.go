package party

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/model"
	"github.com/terminus/party-invite/internal/store"
)

type DAO struct {
	Store *store.Store
	Clock clock.Clock
}

func NewDAO(st *store.Store, clk clock.Clock) *DAO {
	return &DAO{Store: st, Clock: clk}
}

func newID(prefix string) string {
	buf := make([]byte, 8)
	_, _ = rand.Read(buf)
	return prefix + hex.EncodeToString(buf)
}

func (d *DAO) CreateParty(leaderID string, maxMembers int, monoMs int64) (model.PartyRow, error) {
	partyID := newID("pty_")
	_, err := d.Store.DB().Exec(`
INSERT INTO parties (party_id, leader_id, status, max_members, created_mono_ms)
VALUES (?, ?, 'active', ?, ?)
`, partyID, leaderID, maxMembers, monoMs)
	if err != nil {
		return model.PartyRow{}, err
	}
	_, err = d.Store.DB().Exec(`
INSERT INTO members (party_id, player_id, role, status, joined_mono_ms)
VALUES (?, ?, 'leader', 'connected', ?)
`, partyID, leaderID, monoMs)
	if err != nil {
		return model.PartyRow{}, err
	}
	return model.PartyRow{
		PartyID:    partyID,
		LeaderID:   leaderID,
		Status:     "active",
		MaxMembers: maxMembers,
		CreatedMs:  monoMs,
	}, nil
}

func (d *DAO) GetParty(partyID string) (model.PartyRow, error) {
	row := d.Store.DB().QueryRow(`
SELECT party_id, leader_id, status, max_members, created_mono_ms FROM parties WHERE party_id=?
`, partyID)
	var p model.PartyRow
	if err := row.Scan(&p.PartyID, &p.LeaderID, &p.Status, &p.MaxMembers, &p.CreatedMs); err != nil {
		return model.PartyRow{}, err
	}
	return p, nil
}

func (d *DAO) EffectiveOccupancy(partyID string, monoMs int64) (int, error) {
	connected, err := d.Store.CountConnectedMembers(partyID)
	if err != nil {
		return 0, err
	}
	var pending int
	if err := d.Store.DB().QueryRow(`
SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending' AND expires_mono_ms > ?
`, partyID, monoMs).Scan(&pending); err != nil {
		return 0, err
	}
	return connected + pending, nil
}

func (d *DAO) pendingOccupancyExcluding(partyID, excludeInviteID string, monoMs int64) (int, error) {
	connected, err := d.Store.CountConnectedMembers(partyID)
	if err != nil {
		return 0, err
	}
	var pending int
	if err := d.Store.DB().QueryRow(`
SELECT COUNT(1) FROM invites
WHERE party_id=? AND status='pending' AND expires_mono_ms > ? AND invite_id <> ?
`, partyID, monoMs, excludeInviteID).Scan(&pending); err != nil {
		return 0, err
	}
	return connected + pending, nil
}

func (d *DAO) CreateInvite(partyID, inviteeID string, ttlMs, monoMs int64) (model.InviteRow, error) {
	expires := monoMs + ttlMs
	inviteID := newID("inv_")
	_, err := d.Store.DB().Exec(`
INSERT INTO invites (invite_id, party_id, invitee_id, status, expires_mono_ms, created_mono_ms)
VALUES (?, ?, ?, 'pending', ?, ?)
`, inviteID, partyID, inviteeID, expires, monoMs)
	if err != nil {
		return model.InviteRow{}, err
	}
	_ = WriteAuditSnapshot(d.Store, d.Clock, partyID, monoMs)
	return model.InviteRow{
		InviteID:  inviteID,
		PartyID:   partyID,
		InviteeID: inviteeID,
		Status:    "pending",
		ExpiresMs: expires,
		CreatedMs: monoMs,
	}, nil
}

func (d *DAO) GetInvite(inviteID string) (model.InviteRow, error) {
	row := d.Store.DB().QueryRow(`
SELECT invite_id, party_id, invitee_id, status, expires_mono_ms, created_mono_ms
FROM invites WHERE invite_id=?
`, inviteID)
	var inv model.InviteRow
	if err := row.Scan(&inv.InviteID, &inv.PartyID, &inv.InviteeID, &inv.Status, &inv.ExpiresMs, &inv.CreatedMs); err != nil {
		return model.InviteRow{}, err
	}
	return inv, nil
}

func (d *DAO) LookupIdempotency(key string) (model.IdempotencyRecord, bool, error) {
	row := d.Store.DB().QueryRow(`
SELECT idempotency_key, status_code, body_json FROM idempotency WHERE idempotency_key=?
`, key)
	var rec model.IdempotencyRecord
	if err := row.Scan(&rec.Key, &rec.StatusCode, &rec.BodyJSON); err != nil {
		if err == sql.ErrNoRows {
			return model.IdempotencyRecord{}, false, nil
		}
		return model.IdempotencyRecord{}, false, err
	}
	return rec, true, nil
}

func (d *DAO) SaveIdempotency(key string, status int, body any, monoMs int64) error {
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	_, err = d.Store.DB().Exec(`
INSERT INTO idempotency (idempotency_key, status_code, body_json, created_mono_ms)
VALUES (?, ?, ?, ?)
`, key, status, string(raw), monoMs)
	return err
}

func (d *DAO) AcceptInvite(inviteID, inviteeID, idempotencyKey string) (model.AcceptResult, int, error) {
	monoMs := d.Clock.NowMonoMs()

	if idempotencyKey != "" {
		rec, found, err := d.LookupIdempotency(idempotencyKey)
		if err != nil {
			return model.AcceptResult{}, 0, err
		}
		if found {
			var cached model.AcceptResult
			if err := json.Unmarshal([]byte(rec.BodyJSON), &cached); err != nil {
				return model.AcceptResult{}, 0, err
			}
			return cached, rec.StatusCode, nil
		}
	}

	inv, err := d.GetInvite(inviteID)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	if inv.InviteeID != inviteeID {
		return model.AcceptResult{}, 400, fmt.Errorf("invitee mismatch")
	}

	party, err := d.GetParty(inv.PartyID)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	if party.Status != "active" {
		return model.AcceptResult{}, 409, fmt.Errorf("party disbanded")
	}
	leaderOK, err := d.Store.LeaderConnected(inv.PartyID)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	if !leaderOK {
		return model.AcceptResult{}, 409, fmt.Errorf("leader disconnected")
	}
	if inv.Status != "pending" {
		return model.AcceptResult{}, 409, fmt.Errorf("invite not pending")
	}
	if monoMs >= inv.ExpiresMs {
		return model.AcceptResult{}, 409, fmt.Errorf("invite expired")
	}
	occ, err := d.pendingOccupancyExcluding(inv.PartyID, inviteID, monoMs)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	if occ >= party.MaxMembers {
		return model.AcceptResult{}, 409, fmt.Errorf("party full")
	}

	tx, err := d.Store.DB().Begin()
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	defer func() { _ = tx.Rollback() }()

	_, err = tx.Exec(`UPDATE invites SET status='accepted' WHERE invite_id=?`, inviteID)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	_, err = tx.Exec(`
INSERT INTO members (party_id, player_id, role, status, joined_mono_ms)
VALUES (?, ?, 'member', 'connected', ?)
`, inv.PartyID, inviteeID, monoMs)
	if err != nil {
		return model.AcceptResult{}, 0, err
	}
	if err := tx.Commit(); err != nil {
		return model.AcceptResult{}, 0, err
	}

	result := model.AcceptResult{
		PartyID:   inv.PartyID,
		InviteeID: inviteeID,
		Status:    "joined",
	}

	if idempotencyKey != "" {
		_ = d.SaveIdempotency(idempotencyKey, 200, result, monoMs)
	}

	_ = WriteAuditSnapshot(d.Store, d.Clock, inv.PartyID, monoMs)
	return result, 200, nil
}

func (d *DAO) Disconnect(partyID, playerID string) (string, error) {
	party, err := d.GetParty(partyID)
	if err != nil {
		return "", err
	}
	monoMs := d.Clock.NowMonoMs()

	if playerID == party.LeaderID {
		_, err = d.Store.DB().Exec(`UPDATE parties SET status='disbanded' WHERE party_id=?`, partyID)
		if err != nil {
			return "", err
		}
		_, err = d.Store.DB().Exec(`
UPDATE members SET status='disconnected' WHERE party_id=?
`, partyID)
		if err != nil {
			return "", err
		}
		if err := d.RevokePendingInvites(partyID); err != nil {
			return "", err
		}
		_ = WriteAuditSnapshot(d.Store, d.Clock, partyID, monoMs)
		return "disbanded", nil
	}

	_, err = d.Store.DB().Exec(`
UPDATE members SET status='disconnected' WHERE party_id=? AND player_id=?
`, partyID, playerID)
	if err != nil {
		return "", err
	}
	_ = WriteAuditSnapshot(d.Store, d.Clock, partyID, monoMs)
	return party.Status, nil
}

func (d *DAO) BuildAudit(partyID string, monoMs int64) (model.AuditReport, error) {
	return BuildAuditReport(d, partyID, monoMs)
}

func (d *DAO) RevokePendingInvites(partyID string) error {
	_, err := d.Store.DB().Exec(`
UPDATE invites SET status='revoked' WHERE party_id=? AND status='pending'
`, partyID)
	return err
}

func (d *DAO) WallClockMs() int64 {
	return time.Now().UnixMilli()
}
