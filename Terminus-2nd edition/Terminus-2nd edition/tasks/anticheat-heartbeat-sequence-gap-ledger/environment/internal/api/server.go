package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/terminus/livattest-gate/internal/clock"
	"github.com/terminus/livattest-gate/internal/config"
	"github.com/terminus/livattest-gate/internal/export"
	"github.com/terminus/livattest-gate/internal/model"
	"github.com/terminus/livattest-gate/internal/policy"
	"github.com/terminus/livattest-gate/internal/seal"
	"github.com/terminus/livattest-gate/internal/store"
	"github.com/terminus/livattest-gate/internal/vault"
)

const exportPath = "/app/output/attest-report.json"

type Server struct {
	Store  *store.Store
	Cfg    config.Config
	Clock  *clock.Mono
	Vault  *vault.Manager
	Admit  *policy.Admittor
	Export *export.Publisher
}

func New(st *store.Store, cfg config.Config, clk *clock.Mono) (*Server, error) {
	key, err := cfg.VaultKeyBytes()
	if err != nil {
		return nil, err
	}
	v := &vault.Manager{Store: st, VaultKey: key}
	seals := &seal.Manager{Store: st, GraceMs: cfg.GraceMs}
	admit := &policy.Admittor{
		Vault:    v,
		Seals:    seals,
		Clock:    clk,
		SkewTol:  cfg.SkewToleranceMs,
		VaultKey: key,
	}
	return &Server{
		Store:  st,
		Cfg:    cfg,
		Clock:  clk,
		Vault:  v,
		Admit:  admit,
		Export: &export.Publisher{Store: st},
	}, nil
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/trust/bind", s.handleBind)
	mux.HandleFunc("/v1/attest/batch", s.handleBatch)
	mux.HandleFunc("/v1/attest/export", s.handleExport)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleBind(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	var req model.BindRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Token == "" || req.SessionID == "" {
		http.Error(w, "token and session_id required", http.StatusBadRequest)
		return
	}
	tix, err := s.Vault.Bind(req, s.Clock.NowMonoMs())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "bound", "admission_ticket": tix})
}

func (s *Server) handleBatch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	var req model.BatchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Token == "" || req.SessionID == "" || len(req.Beats) == 0 {
		http.Error(w, "token, session_id, and beats required", http.StatusBadRequest)
		return
	}
	if err := s.Admit.ProcessBatch(req); err != nil {
		msg := err.Error()
		switch {
		case strings.Contains(msg, "required"), strings.Contains(msg, "not bound"), strings.Contains(msg, "ticket"):
			http.Error(w, msg, http.StatusBadRequest)
		case strings.Contains(msg, "skew"), strings.Contains(msg, "duplicate"):
			http.Error(w, msg, http.StatusConflict)
		default:
			http.Error(w, msg, http.StatusInternalServerError)
		}
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "accepted"})
}

func (s *Server) handleExport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	var req model.ExportRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Token == "" || req.SessionID == "" {
		http.Error(w, "token and session_id required", http.StatusBadRequest)
		return
	}
	report, err := s.Export.Build(req.Token, req.SessionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if err := s.Export.Write(exportPath, report); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"path": exportPath})
}

func (s *Server) applyMonoHeader(r *http.Request) {
	if raw := r.Header.Get("X-Test-Mono-Ms"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil {
			s.Clock.SetMonoMs(v)
		}
	}
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
