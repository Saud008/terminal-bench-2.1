package server

import (
	"encoding/json"
	"io"
	"net/http"
	"sync"

	"promingest/internal/exemplar"
	"promingest/internal/export"
	"promingest/internal/ingest"
	"promingest/internal/model"
	"promingest/internal/relabel"
)

type Server struct {
	mu     sync.RWMutex
	series map[string][]model.Series
}

func New() *Server {
	return &Server{series: map[string][]model.Series{}}
}

func (s *Server) Reset() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.series = map[string][]model.Series{}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})
	mux.HandleFunc("/api/v1/reset", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		s.Reset()
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("/api/v1/write", s.handleWrite)
	mux.HandleFunc("/api/v1/snapshot", s.handleSnapshot)
	return mux
}

func (s *Server) handleWrite(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	req, err := ingest.DecodeWriteBlock(body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	processed := make([]model.Series, len(req.Series))
	for i := range req.Series {
		series := req.Series[i]
		relabel.ApplySeries(&series)
		exemplar.BindSeries(&series)
		processed[i] = series
	}
	s.mu.Lock()
	s.series[req.Seed] = processed
	s.mu.Unlock()
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleSnapshot(w http.ResponseWriter, r *http.Request) {
	seed := r.URL.Query().Get("seed")
	if seed == "" {
		http.Error(w, "seed required", http.StatusBadRequest)
		return
	}
	s.mu.RLock()
	series := append([]model.Series(nil), s.series[seed]...)
	s.mu.RUnlock()
	snap := export.BuildSnapshot(seed, 0, series)
	w.Header().Set("Content-Type", "application/json")
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	_ = enc.Encode(snap)
}
