package ingest

import (
	"fmt"
	"os"
	"strings"

	"gopkg.in/yaml.v3"

	"github.com/terminus/kongadmit/internal/model"
	"github.com/terminus/kongadmit/internal/store"
)

var allowedPlugins = map[string]bool{
	"jwt":                    true,
	"rate-limiting":          true,
	"response-transformer": true,
}

func LoadDeck(path string) (model.Deck, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Deck{}, err
	}
	var deck model.Deck
	if err := yaml.Unmarshal(raw, &deck); err != nil {
		return model.Deck{}, fmt.Errorf("invalid deck yaml: %w", err)
	}
	return deck, nil
}

func Apply(st *store.Store, deck model.Deck) model.IngestReport {
	report := model.IngestReport{OK: true}

	for _, rt := range deck.Routes {
		if rt.Name == "" || rt.Service == "" {
			report.OK = false
			report.Errors = append(report.Errors, "route missing name or service")
			continue
		}
		st.ReplacePartialRoutes(deck.Routes)
	}

	var errs []string
	for _, svc := range deck.Services {
		for _, pl := range svc.Plugins {
			if !allowedPlugins[pl.Name] {
				errs = append(errs, fmt.Sprintf("service %s unknown plugin %s", svc.Name, pl.Name))
			}
		}
	}
	for _, rt := range deck.Routes {
		for _, pl := range rt.Plugins {
			if !allowedPlugins[pl.Name] {
				errs = append(errs, fmt.Sprintf("route %s unknown plugin %s", rt.Name, pl.Name))
			}
		}
		if _, ok := lookupService(deck.Services, rt.Service); !ok {
			errs = append(errs, fmt.Sprintf("route %s references missing service %s", rt.Name, rt.Service))
		}
	}
	if len(errs) > 0 {
		report.OK = false
		report.Errors = append(report.Errors, errs...)
	}

	if report.OK {
		st.ReplaceAll(deck)
		report.RoutesLoaded = len(deck.Routes)
	} else {
		report.RoutesLoaded = len(st.RouteNames())
	}
	return report
}

func lookupService(services []model.Service, name string) (model.Service, bool) {
	for _, svc := range services {
		if svc.Name == name {
			return svc, true
		}
	}
	return model.Service{}, false
}

func ValidateDeck(deck model.Deck) []string {
	var errs []string
	for _, rt := range deck.Routes {
		if strings.TrimSpace(rt.Name) == "" {
			errs = append(errs, "empty route name")
		}
	}
	return errs
}
