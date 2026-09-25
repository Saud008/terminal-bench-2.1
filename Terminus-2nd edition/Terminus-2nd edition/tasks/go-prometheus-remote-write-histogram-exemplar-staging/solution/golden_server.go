package server

import (
	"encoding/json"
	"io"
	"net/http"

	"promingest/internal/exemplar"
	"promingest/internal/export"
	"promingest/internal/ingest"
	"promingest/internal/model"
	"promingest/internal/relabel"
	"promingest/internal/staging"
)

type Server struct{}

func New() *Server {
	return &Server{}
}

func (s *Server) Reset() {}

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
	if err := staging.Write(req); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleSnapshot(w http.ResponseWriter, r *http.Request) {
	seed := r.URL.Query().Get("seed")
	if seed == "" {
		http.Error(w, "seed required", http.StatusBadRequest)
		return
	}
	rec, err := staging.Read(seed)
	if err != nil {
		snap := model.Snapshot{Seed: seed, Sequence: 0, Series: []model.SnapshotSeries{}}
		w.Header().Set("Content-Type", "application/json")
		enc := json.NewEncoder(w)
		enc.SetIndent("", "  ")
		_ = enc.Encode(snap)
		return
	}
	processed := make([]model.Series, len(rec.Series))
	for i := range rec.Series {
		series := rec.Series[i]
		relabel.ApplySeries(&series)
		exemplar.BindSeries(&series)
		processed[i] = series
	}
	snap := export.BuildSnapshot(seed, rec.Sequence, processed)
	w.Header().Set("Content-Type", "application/json")
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	_ = enc.Encode(snap)
}
