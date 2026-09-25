package gateway

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/terminus/jktadmit-gate/internal/auditseal"
	"github.com/terminus/jktadmit-gate/internal/gateflow"
	"github.com/terminus/jktadmit-gate/internal/jktpin"
	"github.com/terminus/jktadmit-gate/internal/schema"
	"github.com/terminus/jktadmit-gate/internal/sessionstore"
	"github.com/terminus/jktadmit-gate/internal/settings"
	"github.com/terminus/jktadmit-gate/internal/timepin"
)

type Server struct {
	Store  *sessionstore.Store
	Cfg    settings.Config
	Clock  *timepin.Pinned
	Pin    *jktpin.Manager
	Gate   *gateflow.Gate
	Seal   *auditseal.Publisher
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/gate/session/open", s.handleOpen)
	mux.HandleFunc("/gate/proof/check", s.handleCheck)
	mux.HandleFunc("/gate/audit/commit", s.handleCommit)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleOpen(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyNowHeader(r)
	var req schema.OpenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Principal == "" || req.Session == "" || req.DPoPProof == "" {
		http.Error(w, "principal, session, and dpop_proof required", http.StatusBadRequest)
		return
	}
	tix, jkt, err := s.Pin.Open(req, s.Clock.NowUnix())
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "opened", "bind_ticket": tix, "jkt": jkt})
}

func (s *Server) handleCheck(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyNowHeader(r)
	var req schema.CheckRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Principal == "" || req.Session == "" || req.DPoPProof == "" {
		http.Error(w, "principal, session, and dpop_proof required", http.StatusBadRequest)
		return
	}
	result, err := s.Gate.Check(req, s.Clock.NowUnix())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	code := http.StatusOK
	if result.Verdict != "admit" {
		code = http.StatusConflict
	}
	writeJSON(w, code, map[string]string{"verdict": result.Verdict, "reason": result.Reason})
}

func (s *Server) handleCommit(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req schema.CommitRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Principal == "" || req.Session == "" {
		http.Error(w, "principal and session required", http.StatusBadRequest)
		return
	}
	ledger, err := s.Seal.Build(req.Principal, req.Session)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := s.Seal.Write(auditseal.LedgerPath, ledger); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"path": auditseal.LedgerPath})
}

func (s *Server) applyNowHeader(r *http.Request) {
	if raw := r.Header.Get("X-Test-Now-Unix"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil {
			s.Clock.SetUnix(v)
		}
	}
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
