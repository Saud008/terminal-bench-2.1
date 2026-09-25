package api

import (
	"encoding/json"
	"net/http"
	"os"

	"github.com/terminus/kongadmit/internal/export"
	"github.com/terminus/kongadmit/internal/ingest"
	"github.com/terminus/kongadmit/internal/store"
)

type Admin struct {
	Store    *store.Store
	DeckPath string
}

func (a *Admin) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch {
	case r.Method == http.MethodGet && r.URL.Path == "/health":
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	case r.Method == http.MethodPost && r.URL.Path == "/admin/ingest":
		a.handleIngest(w, r)
	case r.Method == http.MethodPost && r.URL.Path == "/admin/reload":
		a.handleReload(w, r)
	case r.Method == http.MethodGet && r.URL.Path == "/admin/export/openapi":
		a.handleExport(w, r)
	case r.Method == http.MethodPost && r.URL.Path == "/admin/reset-rates":
		a.Store.ResetRates()
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(map[string]bool{"ok": true})
	default:
		http.NotFound(w, r)
	}
}

func (a *Admin) handleIngest(w http.ResponseWriter, r *http.Request) {
	var body struct {
		DeckPath string `json:"deck_path"`
	}
	if r.Body != nil {
		_ = json.NewDecoder(r.Body).Decode(&body)
	}
	path := body.DeckPath
	if path == "" {
		path = a.DeckPath
	}
	deck, err := ingest.LoadDeck(path)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(modelIngestErr(err))
		return
	}
	report := ingest.Apply(a.Store, deck)
	status := http.StatusOK
	if !report.OK {
		status = http.StatusUnprocessableEntity
	}
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(report)
}

func (a *Admin) handleReload(w http.ResponseWriter, r *http.Request) {
	if _, err := os.Stat(a.DeckPath); err != nil {
		http.Error(w, "deck missing", http.StatusBadRequest)
		return
	}
	deck, err := ingest.LoadDeck(a.DeckPath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	report := ingest.Apply(a.Store, deck)
	status := http.StatusOK
	if !report.OK {
		status = http.StatusUnprocessableEntity
	}
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(report)
}

func (a *Admin) handleExport(w http.ResponseWriter, r *http.Request) {
	services, routes, _ := a.Store.Snapshot()
	spec := export.BuildOpenAPI(routes, services)
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(spec)
}

func modelIngestErr(err error) map[string]any {
	return map[string]any{"ok": false, "errors": []string{err.Error()}}
}
