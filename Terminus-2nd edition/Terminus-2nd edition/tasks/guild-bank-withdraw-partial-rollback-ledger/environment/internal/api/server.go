package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/example/vaultcore/internal/bank"
	"github.com/example/vaultcore/internal/clock"
	"github.com/example/vaultcore/internal/config"
	"github.com/example/vaultcore/internal/interest"
	"github.com/example/vaultcore/internal/model"
	"github.com/example/vaultcore/internal/store"
)

const exportPath = "/app/output/guild-audit.json"

type Server struct {
	Store    *store.Store
	Cfg      config.Config
	Clock    *clock.Mono
	Bank     *bank.Handler
	Interest *interest.Accrual
}

func New(st *store.Store, cfg config.Config, clk *clock.Mono) *Server {
	dao := bank.NewDAO(st, clk, cfg)
	return &Server{
		Store:    st,
		Cfg:      cfg,
		Clock:    clk,
		Bank:     bank.NewHandler(dao, cfg),
		Interest: interest.New(st, clk),
	}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/guild/bootstrap", s.handleBootstrap)
	mux.HandleFunc("/v1/guild/", s.handleGuildSub)
	mux.HandleFunc("/v1/admin/interest/", s.handleInterest)
	mux.HandleFunc("/v1/guild/export", s.handleExport)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) applyMonoHeader(r *http.Request) {
	if raw := r.Header.Get("X-Test-Mono-Ms"); raw != "" {
		if v, err := strconv.ParseInt(raw, 10, 64); err == nil {
			s.Clock.SetOverride(v)
			return
		}
	}
	s.Clock.ClearOverride()
}

func (s *Server) handleBootstrap(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	var req model.BootstrapRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.GuildID == "" || req.InitialGold < 0 {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	row, err := s.Bank.Bootstrap(req.GuildID, req.InitialGold, req.InterestRateBps)
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"guild_id":          row.GuildID,
		"gold_balance":      row.GoldBalance,
		"interest_rate_bps": row.InterestRateBps,
	})
}

func (s *Server) handleGuildSub(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	path := strings.TrimPrefix(r.URL.Path, "/v1/guild/")
	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) < 2 {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	guildID := parts[0]
	action := parts[1]
	switch action {
	case "deposit":
		if len(parts) < 3 || parts[2] != "stack" {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		s.handleDepositStack(w, r, guildID)
	case "withdraw":
		if len(parts) < 3 {
			http.Error(w, "not found", http.StatusNotFound)
			return
		}
		switch parts[2] {
		case "gold":
			s.handleWithdrawGold(w, r, guildID)
		case "stack":
			s.handleWithdrawStack(w, r, guildID)
		default:
			http.Error(w, "not found", http.StatusNotFound)
		}
	case "transfer-out":
		s.handleTransferOut(w, r, guildID)
	default:
		http.Error(w, "not found", http.StatusNotFound)
	}
}

func (s *Server) handleDepositStack(w http.ResponseWriter, r *http.Request, guildID string) {
	var req model.DepositStackRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.ItemTemplateID == "" || req.Quantity <= 0 {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	row, err := s.Bank.DepositStack(guildID, req.ItemTemplateID, req.Quantity, req.Bound)
	if mapErr(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"stack_id":         row.StackID,
		"item_template_id": row.ItemTemplateID,
		"quantity":         row.Quantity,
		"bound":            row.Bound,
	})
}

func (s *Server) handleWithdrawGold(w http.ResponseWriter, r *http.Request, guildID string) {
	var req model.WithdrawGoldRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.PlayerID == "" || req.Amount <= 0 {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	bal, err := s.Bank.WithdrawGold(guildID, req.PlayerID, req.Amount)
	if mapErr(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"guild_id":     guildID,
		"player_id":    req.PlayerID,
		"gold_balance": bal,
	})
}

func (s *Server) handleWithdrawStack(w http.ResponseWriter, r *http.Request, guildID string) {
	var req model.WithdrawStackRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.PlayerID == "" || req.StackID == "" || req.Quantity <= 0 {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	row, err := s.Bank.WithdrawStack(guildID, req.PlayerID, req.StackID, req.Quantity)
	if mapErr(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"slice_id":         row.SliceID,
		"player_id":        row.PlayerID,
		"item_template_id": row.ItemTemplateID,
		"quantity":         row.Quantity,
	})
}

func (s *Server) handleTransferOut(w http.ResponseWriter, r *http.Request, guildID string) {
	var req model.TransferOutRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.PlayerID == "" || req.StackID == "" {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	playerStackID, err := s.Bank.TransferOut(guildID, req.PlayerID, req.StackID)
	if mapErr(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"player_stack_id": playerStackID,
		"player_id":       req.PlayerID,
	})
}

func (s *Server) handleInterest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	s.applyMonoHeader(r)
	path := strings.TrimPrefix(r.URL.Path, "/v1/admin/interest/")
	switch strings.Trim(path, "/") {
	case "run":
		s.handleInterestRun(w, r)
	case "replay":
		s.handleInterestReplay(w, r)
	default:
		http.Error(w, "not found", http.StatusNotFound)
	}
}

func (s *Server) handleInterestRun(w http.ResponseWriter, r *http.Request) {
	var req model.InterestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.GuildID == "" || req.PeriodID == "" {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	res, err := s.Interest.Run(req.GuildID, req.PeriodID)
	if mapErr(w, err) {
		return
	}
	writeJSON(w, http.StatusOK, res)
}

func (s *Server) handleInterestReplay(w http.ResponseWriter, r *http.Request) {
	var req model.InterestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.GuildID == "" || req.PeriodID == "" {
		http.Error(w, "missing fields", http.StatusBadRequest)
		return
	}
	res, err := s.Interest.Replay(req.GuildID, req.PeriodID)
	if mapErr(w, err) {
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
	if req.GuildID == "" {
		http.Error(w, "guild_id required", http.StatusBadRequest)
		return
	}
	report, err := s.Bank.Export(req.GuildID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
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

func mapErr(w http.ResponseWriter, err error) bool {
	if err == nil {
		return false
	}
	msg := err.Error()
	if strings.Contains(msg, "insufficient") ||
		strings.Contains(msg, "exceeds") ||
		strings.Contains(msg, "bound") ||
		strings.Contains(msg, "invalid") ||
		strings.Contains(msg, "mismatch") ||
		strings.Contains(msg, "missing") {
		http.Error(w, msg, http.StatusConflict)
		return true
	}
	if errors.Is(err, os.ErrNotExist) {
		http.Error(w, msg, http.StatusConflict)
		return true
	}
	http.Error(w, msg, http.StatusInternalServerError)
	return true
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
