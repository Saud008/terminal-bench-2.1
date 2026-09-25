package store

import (
	"sync"

	"github.com/terminus/kongadmit/internal/model"
)

type Store struct {
	mu        sync.RWMutex
	Services  map[string]model.Service
	Routes    map[string]model.Route
	Consumers map[string]model.Consumer
	Rate      model.RateState
}

func New() *Store {
	return &Store{
		Services:  make(map[string]model.Service),
		Routes:    make(map[string]model.Route),
		Consumers: make(map[string]model.Consumer),
		Rate: model.RateState{
			Counts: make(map[string]int),
			Limit:  5,
		},
	}
}

func (s *Store) ReplaceAll(deck model.Deck) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Services = make(map[string]model.Service)
	s.Routes = make(map[string]model.Route)
	s.Consumers = make(map[string]model.Consumer)
	for _, svc := range deck.Services {
		s.Services[svc.Name] = svc
	}
	for _, rt := range deck.Routes {
		s.Routes[rt.Name] = rt
	}
	for _, c := range deck.Consumers {
		s.Consumers[c.Username] = c
	}
	s.Rate.Counts = make(map[string]int)
}

func (s *Store) Snapshot() (services map[string]model.Service, routes map[string]model.Route, consumers map[string]model.Consumer) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	services = make(map[string]model.Service, len(s.Services))
	routes = make(map[string]model.Route, len(s.Routes))
	consumers = make(map[string]model.Consumer, len(s.Consumers))
	for k, v := range s.Services {
		services[k] = v
	}
	for k, v := range s.Routes {
		routes[k] = v
	}
	for k, v := range s.Consumers {
		consumers[k] = v
	}
	return services, routes, consumers
}

func (s *Store) RateLimitKey(routeName, clientKey string) string {
	return routeName + ":" + clientKey
}

func (s *Store) IncrRate(key string) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Rate.Counts[key]++
	return s.Rate.Counts[key]
}

func (s *Store) RateLimit() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.Rate.Limit
}

func (s *Store) ResetRates() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Rate.Counts = make(map[string]int)
}
