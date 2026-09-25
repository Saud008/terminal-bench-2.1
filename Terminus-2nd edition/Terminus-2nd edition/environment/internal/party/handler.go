package party

import (
	"database/sql"
	"fmt"

	"github.com/terminus/party-invite/internal/config"
	"github.com/terminus/party-invite/internal/model"
)

type Handler struct {
	DAO    *DAO
	Config config.Config
}

func NewHandler(dao *DAO, cfg config.Config) *Handler {
	return &Handler{DAO: dao, Config: cfg}
}

func (h *Handler) Create(leaderID string, maxMembers int, monoMs int64) (model.PartyRow, error) {
	if leaderID == "" {
		return model.PartyRow{}, fmt.Errorf("leader_id required")
	}
	cap := config.ClampMaxMembers(maxMembers, h.Config.MaxMembers)
	return h.DAO.CreateParty(leaderID, cap, monoMs)
}

func (h *Handler) Invite(partyID, inviteeID string, ttlMs, monoMs int64) (model.InviteRow, error) {
	if inviteeID == "" {
		return model.InviteRow{}, fmt.Errorf("invitee_id required")
	}
	party, err := h.DAO.GetParty(partyID)
	if err != nil {
		if err == sql.ErrNoRows {
			return model.InviteRow{}, fmt.Errorf("party not found")
		}
		return model.InviteRow{}, err
	}
	if party.Status != "active" {
		return model.InviteRow{}, fmt.Errorf("party disbanded")
	}
	leaderOK, err := h.DAO.Store.LeaderConnected(partyID)
	if err != nil {
		return model.InviteRow{}, err
	}
	if !leaderOK {
		return model.InviteRow{}, fmt.Errorf("leader disconnected")
	}
	if ttlMs <= 0 {
		ttlMs = h.Config.DefaultInviteTTLMs
	}
	occ, err := h.DAO.EffectiveOccupancy(partyID, monoMs)
	if err != nil {
		return model.InviteRow{}, err
	}
	if occ >= party.MaxMembers {
		return model.InviteRow{}, fmt.Errorf("party full")
	}
	return h.DAO.CreateInvite(partyID, inviteeID, ttlMs, monoMs)
}

func (h *Handler) Accept(inviteID, inviteeID, idempotencyKey string) (model.AcceptResult, int, error) {
	if idempotencyKey == "" {
		return model.AcceptResult{}, 400, fmt.Errorf("idempotency key required")
	}
	if inviteeID == "" {
		return model.AcceptResult{}, 400, fmt.Errorf("invitee_id required")
	}
	return h.DAO.AcceptInvite(inviteID, inviteeID, idempotencyKey)
}

func (h *Handler) Disconnect(partyID, playerID string) (string, error) {
	if playerID == "" {
		return "", fmt.Errorf("player_id required")
	}
	return h.DAO.Disconnect(partyID, playerID)
}

func (h *Handler) Export(partyID string, monoMs int64) (model.AuditReport, error) {
	if partyID == "" {
		return model.AuditReport{}, fmt.Errorf("party_id required")
	}
	return h.DAO.BuildAudit(partyID, monoMs)
}
