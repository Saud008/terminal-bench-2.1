package api

import (
	"encoding/json"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/terminus/party-invite/internal/cleanup"
	"github.com/terminus/party-invite/internal/clock"
	"github.com/terminus/party-invite/internal/config"
	"github.com/terminus/party-invite/internal/model"
	"github.com/terminus/party-invite/internal/party"
	"github.com/terminus/party-invite/internal/store"
)

const exportPath = "/app/output/party-audit.json"

type Server struct {
	Store   *store.Store
	Cfg     config.Config
	Clock   *clock.Mono
	Party   *party.Handler
	Sweeper *cleanup.Sweeper
}

func New(st *store.Store, cfg config.Config, clk *clock.Mono) *Server {
	dao := party.NewDAO(st, clk)
	return &Server{
		Store:   st,
		Cfg:     cfg,
		Clock:   clk,
		Party:   party.NewHandler(dao, cfg),
		Sweeper: cleanup.New(st, clk),
	}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/party/create", s.handleCreate)
	mux.HandleFunc("/v1/party/", s.handlePartySub)
	mux.HandleFunc("/v1/invite/", s.handleInviteSub)
	mux.HandleFunc("/v1/admin/sweep", s.handleSweep)
	mux.HandleFunc("/v1/party/export", s.handleExport)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleCreate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	var req model.CreatePartyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.LeaderID == "" {
		http.Error(w, "leader_id required", http.StatusBadRequest)
		return
	}
	row, err := s.Party.Create(req.LeaderID, req.MaxMembers, s.Clock.NowMonoMs())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"party_id":     row.PartyID,
		"leader_id":    row.LeaderID,
		"max_members":  row.MaxMembers,
	})
}

func (s *Server) handlePartySub(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/v1/party/")
	if path == "export" {
		s.handleExport(w, r)
		return
	}
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 2 {
		http.NotFound(w, r)
		return
	}
	partyID, action := parts[0], parts[1]
	s.applyMonoHeader(r)
	switch action {
	case "invite":
		s.handleInvite(w, r, partyID)
	case "disconnect":
		s.handleDisconnect(w, r, partyID)
	default:
		http.NotFound(w, r)
	}
}

func (s *Server) handleInvite(w http.ResponseWriter, r *http.Request, partyID string) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.InviteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.InviteeID == "" {
		http.Error(w, "invitee_id required", http.StatusBadRequest)
		return
	}
	inv, err := s.Party.Invite(partyID, req.InviteeID, req.TTLMs, s.Clock.NowMonoMs())
	if err != nil {
		msg := err.Error()
		switch {
		case strings.Contains(msg, "required"), strings.Contains(msg, "not found"):
			http.Error(w, msg, http.StatusBadRequest)
		case strings.Contains(msg, "disbanded"), strings.Contains(msg, "disconnected"), strings.Contains(msg, "full"):
			http.Error(w, msg, http.StatusConflict)
		default:
			http.Error(w, msg, http.StatusInternalServerError)
		}
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"invite_id":         inv.InviteID,
		"expires_mono_ms":   inv.ExpiresMs,
	})
}

func (s *Server) handleInviteSub(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/v1/invite/")
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) != 2 || parts[1] != "accept" {
		http.NotFound(w, r)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	idempotencyKey := r.Header.Get("Idempotency-Key")
	var req model.AcceptRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	result, code, err := s.Party.Accept(parts[0], req.InviteeID, idempotencyKey)
	if err != nil {
		msg := err.Error()
		switch {
		case strings.Contains(msg, "required"), strings.Contains(msg, "mismatch"):
			http.Error(w, msg, http.StatusBadRequest)
		case strings.Contains(msg, "disbanded"), strings.Contains(msg, "disconnected"),
			strings.Contains(msg, "expired"), strings.Contains(msg, "pending"), strings.Contains(msg, "full"):
			http.Error(w, msg, http.StatusConflict)
		default:
			http.Error(w, msg, http.StatusInternalServerError)
		}
		return
	}
	writeJSON(w, code, result)
}

func (s *Server) handleDisconnect(w http.ResponseWriter, r *http.Request, partyID string) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.DisconnectRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	status, err := s.Party.Disconnect(partyID, req.PlayerID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"party_id": partyID,
		"status":   status,
	})
}

func (s *Server) handleSweep(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	res, err := s.Sweeper.Run()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, res)
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
	report, err := s.Party.Export(req.PartyID, s.Clock.NowMonoMs())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := os.WriteFile(exportPath, raw, 0o644); err != nil {
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
