package vault

import (
	"fmt"

	"github.com/terminus/livattest-gate/internal/model"
	"github.com/terminus/livattest-gate/internal/store"
	"github.com/terminus/livattest-gate/internal/ticket"
)

type Manager struct {
	Store    *store.Store
	VaultKey []byte
}

func (m *Manager) Bind(req model.BindRequest, monoMs int64) (string, error) {
	if req.Token == "" || req.SessionID == "" {
		return "", fmt.Errorf("token and session_id required")
	}
	tix := ticket.Mint(m.VaultKey, req.Token, req.SessionID, monoMs)
	sess := model.SessionState{
		Token:           req.Token,
		SessionID:       req.SessionID,
		AnchorClient:    req.ClientMs,
		AnchorMono:      monoMs,
		AdmissionTicket: tix,
	}
	if err := m.Store.UpsertSession(sess); err != nil {
		return "", err
	}
	return tix, nil
}

func (m *Manager) Load(token, sessionID string) (model.SessionState, error) {
	return m.Store.GetSession(token, sessionID)
}

func (m *Manager) Save(sess model.SessionState) error {
	return m.Store.UpsertSession(sess)
}

func (m *Manager) IsDuplicateSeq(token, sessionID string, seq uint32) (bool, error) {
	return m.Store.HasSeenSeq(token, sessionID, seq)
}
