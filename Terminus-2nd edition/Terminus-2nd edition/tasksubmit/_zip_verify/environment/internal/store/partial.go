package store

import "github.com/terminus/kongadmit/internal/model"

func (s *Store) ReplacePartialRoutes(routes []model.Route) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, rt := range routes {
		s.Routes[rt.Name] = rt
	}
}

func (s *Store) RouteNames() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]string, 0, len(s.Routes))
	for name := range s.Routes {
		out = append(out, name)
	}
	return out
}
