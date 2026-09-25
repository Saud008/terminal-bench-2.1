package store

import (
	"sync"

	"github.com/terminus/transit-mock/internal/apperr"
	"github.com/terminus/transit-mock/internal/ledger"
	"github.com/terminus/transit-mock/internal/model"
	"github.com/terminus/transit-mock/internal/policy"
)

type Memory struct {
	mu       sync.RWMutex
	keys     map[string]*model.KeyState
	policyDir string
}

func New(policyDir string) *Memory {
	return &Memory{
		keys:      make(map[string]*model.KeyState),
		policyDir: policyDir,
	}
}

func (m *Memory) LoadPolicy(name, policyFile string) (*model.KeyState, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	pol, err := policy.LoadFromFile(m.policyDir, policyFile)
	if err != nil {
		return nil, err
	}
	key := ledger.NewKey(name, pol)
	m.keys[name] = key
	return cloneKey(key), nil
}

func (m *Memory) Get(name string) (*model.KeyState, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	key, ok := m.keys[name]
	if !ok {
		return nil, apperr.ErrNotFound
	}
	return cloneKey(key), nil
}

func (m *Memory) Rotate(name string) (*model.KeyState, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	key, ok := m.keys[name]
	if !ok {
		return nil, apperr.ErrNotFound
	}
	ledger.Rotate(key)
	return cloneKey(key), nil
}

func (m *Memory) DeleteVersion(name string, version int) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	key, ok := m.keys[name]
	if !ok {
		return apperr.ErrNotFound
	}
	return ledger.DeleteVersion(key, version)
}

func (m *Memory) SetSoftHalt(name string, after int) (*model.KeyState, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	key, ok := m.keys[name]
	if !ok {
		return nil, apperr.ErrNotFound
	}
	ledger.SetSoftHalt(key, after)
	return cloneKey(key), nil
}

func (m *Memory) KeyRef(name string) (*model.KeyState, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	key, ok := m.keys[name]
	if !ok {
		return nil, apperr.ErrNotFound
	}
	return key, nil
}

func cloneKey(key *model.KeyState) *model.KeyState {
	cp := *key
	cp.Versions = append([]model.VersionEntry(nil), key.Versions...)
	cp.Policy = key.Policy
	return &cp
}
