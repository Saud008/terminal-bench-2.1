package seal

import (
	"github.com/terminus/livattest-gate/internal/model"
	"github.com/terminus/livattest-gate/internal/store"
)

type Manager struct {
	Store   *store.Store
	GraceMs int64
}

func InSpan(from, to, seq uint32) bool {
	if from <= to {
		return seq >= from && seq <= to
	}
	return seq >= from || seq <= to
}

func (m *Manager) OpenBreach(token, sessionID string, from, to, span uint32, monoMs int64) (int64, error) {
	id, err := m.Store.OpenBreach(token, sessionID, from, to, span, monoMs)
	if err != nil {
		return 0, err
	}
	if err := m.Store.IssueBan(token, sessionID, id, monoMs); err != nil {
		return 0, err
	}
	return id, nil
}

func (m *Manager) OpenBreaches(token, sessionID string) ([]model.BreachSeal, error) {
	return m.Store.OpenBreaches(token, sessionID)
}

func (m *Manager) TryRepair(token, sessionID string, seq uint32, monoMs int64) (bool, error) {
	open, err := m.Store.OpenBreaches(token, sessionID)
	if err != nil {
		return false, err
	}
	for _, b := range open {
		if !InSpan(b.FromSeq, b.ToSeq, seq) {
			continue
		}
		already, err := m.Store.IsRepaired(b.ID, seq)
		if err != nil {
			return false, err
		}
		if already {
			continue
		}
		if err := m.Store.MarkRepaired(token, sessionID, b.ID, seq); err != nil {
			return false, err
		}
		count, err := m.Store.RepairedCount(b.ID)
		if err != nil {
			return false, err
		}
		if uint32(count) >= b.MissingSpan {
			if err := m.Store.CloseBreach(token, sessionID, b.ID, monoMs); err != nil {
				return false, err
			}
			if err := m.MaybeRevokeBan(b.ID, monoMs); err != nil {
				return false, err
			}
		}
		return true, nil
	}
	return false, nil
}

func (m *Manager) ActiveBanCount(token, sessionID string) (int, error) {
	return m.Store.CountActiveBans(token, sessionID)
}
