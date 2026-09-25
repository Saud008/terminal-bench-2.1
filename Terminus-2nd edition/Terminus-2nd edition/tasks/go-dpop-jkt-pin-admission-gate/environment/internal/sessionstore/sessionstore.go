package sessionstore

import (
	"sync"

	"github.com/terminus/jktadmit-gate/internal/schema"
)

// Store is the process-lifetime session table. A fresh jktadmit process
// always starts with an empty store; there is no cross-restart persistence.
type Store struct {
	mu   sync.Mutex
	data map[string]schema.SessionState
}

func New() *Store {
	return &Store{data: make(map[string]schema.SessionState)}
}

func Key(principal, session string) string {
	return principal + ":" + session
}

func (s *Store) Get(key string) (schema.SessionState, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v, ok := s.data[key]
	if !ok {
		return schema.SessionState{}, false
	}
	return v.Clone(), true
}

func (s *Store) Put(key string, v schema.SessionState) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data[key] = v.Clone()
}

func (s *Store) Reset() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.data = make(map[string]schema.SessionState)
}
