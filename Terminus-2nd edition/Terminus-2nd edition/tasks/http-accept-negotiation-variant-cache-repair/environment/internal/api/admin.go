package api

import (
	"io"
	"net/http"
)

func (s *Server) handleAdminCatalog(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	data, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "read error", http.StatusBadRequest)
		return
	}
	if err := s.Store.LoadFromBytes(data); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	s.Cache.Reset()
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"reloaded"}`))
}
