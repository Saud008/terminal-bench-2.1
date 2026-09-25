package variants

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"

	"github.com/terminus/variantgate/internal/model"
)

type Store struct {
	mu        sync.RWMutex
	resources map[string]model.Resource
}

func Load(path string) (*Store, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cat model.Catalog
	if err := json.Unmarshal(data, &cat); err != nil {
		return nil, err
	}
	if cat.Resources == nil {
		cat.Resources = map[string]model.Resource{}
	}
	return &Store{resources: cat.Resources}, nil
}

func (s *Store) Replace(cat model.Catalog) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if cat.Resources == nil {
		cat.Resources = map[string]model.Resource{}
	}
	s.resources = cat.Resources
}

func (s *Store) Get(id string) (model.Resource, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	res, ok := s.resources[id]
	return res, ok
}

func (s *Store) LoadFromBytes(data []byte) error {
	var cat model.Catalog
	if err := json.Unmarshal(data, &cat); err != nil {
		return fmt.Errorf("invalid catalog: %w", err)
	}
	s.Replace(cat)
	return nil
}
