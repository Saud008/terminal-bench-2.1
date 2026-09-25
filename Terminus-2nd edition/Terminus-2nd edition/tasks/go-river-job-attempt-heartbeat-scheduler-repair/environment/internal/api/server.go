package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

	"github.com/terminus/riverbench/internal/clock"
	"github.com/terminus/riverbench/internal/config"
	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/scheduler"
	"github.com/terminus/riverbench/internal/store"
)

type Server struct {
	Sched       *scheduler.Scheduler
	Store       *store.Store
	Cfg         config.Config
	CatalogPath string
	Clock       clock.Clock
}

func New(st *store.Store, cfg config.Config, catalogPath string, clk clock.Clock) *Server {
	sched := &scheduler.Scheduler{
		Store:       st,
		Clock:       clk,
		LeaseMs:     cfg.LeaseMs,
		BackoffBase: cfg.BackoffBase,
		DefaultMax:  cfg.DefaultMax,
	}
	return &Server{Sched: sched, Store: st, Cfg: cfg, CatalogPath: catalogPath, Clock: clk}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/admin/seed", s.handleSeed)
	mux.HandleFunc("/admin/jobs", s.handleJobs)
	mux.HandleFunc("/admin/leases", s.handleLeases)
	mux.HandleFunc("/admin/inject-heartbeat", s.handleInjectHeartbeat)
	mux.HandleFunc("/admin/force-ready", s.handleForceReady)
	mux.HandleFunc("/worker/claim", s.handleClaim)
	mux.HandleFunc("/worker/", s.handleWorker)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleSeed(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.SeedRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Seed == "" {
		http.Error(w, "seed required", http.StatusBadRequest)
		return
	}
	n, err := scheduler.SeedStore(s.Store, req, s.CatalogPath, s.Cfg.DefaultMax, s.Clock.NowMs())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"seeded": n})
}

func (s *Server) handleJobs(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	state := r.URL.Query().Get("state")
	jobs, err := s.Store.ListJobs(state)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, jobs)
}

func (s *Server) handleLeases(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	leases, err := s.Store.ListLeases()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, leases)
}

type injectReq struct {
	JobID          string `json:"job_id"`
	WorkerID       string `json:"worker_id"`
	ExpiresAtMs    int64  `json:"expires_at_ms"`
	ExpiresAtDelta int64  `json:"expires_at_delta_ms"`
}

func (s *Server) handleForceReady(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		JobID string `json:"job_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	job, err := s.Store.GetJob(req.JobID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	if job.State != model.StatePending {
		http.Error(w, "job not pending", http.StatusBadRequest)
		return
	}
	job.AvailableAt = s.Clock.NowMs()
	if err := s.Store.UpdateJob(job); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"job_id": job.ID})
}

func (s *Server) handleInjectHeartbeat(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req injectReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.JobID == "" || req.WorkerID == "" {
		http.Error(w, "job_id and worker_id required", http.StatusBadRequest)
		return
	}
	now := s.Clock.NowMs()
	exp := req.ExpiresAtMs
	if exp == 0 {
		exp = now + req.ExpiresAtDelta
	}
	if err := s.Store.SetLeaseExpiry(req.JobID, exp); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"job_id": req.JobID, "expires_at_ms": exp})
}

func (s *Server) handleClaim(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var body struct {
		WorkerID string `json:"worker_id"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if body.WorkerID == "" {
		http.Error(w, "worker_id required", http.StatusBadRequest)
		return
	}
	job, err := s.Sched.Claim(body.WorkerID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}
	writeJSON(w, http.StatusOK, job)
}

func (s *Server) handleWorker(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/worker/")
	parts := strings.Split(path, "/")
	if len(parts) < 2 {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	jobID := parts[0]
	action := parts[1]
	var body struct {
		WorkerID string `json:"worker_id"`
		Error    string `json:"error"`
	}
	_ = json.NewDecoder(r.Body).Decode(&body)
	if body.WorkerID == "" {
		http.Error(w, "worker_id required", http.StatusBadRequest)
		return
	}
	switch action {
	case "heartbeat":
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		lease, err := s.Sched.Heartbeat(body.WorkerID, jobID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		writeJSON(w, http.StatusOK, lease)
	case "ack":
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if err := s.Sched.Ack(body.WorkerID, jobID); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "finished"})
	case "fail":
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if err := s.Sched.Fail(body.WorkerID, jobID, body.Error); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "failed"})
	default:
		http.Error(w, "not found", http.StatusNotFound)
	}
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func ListenAndServe(st *store.Store, cfg config.Config, catalogPath string) error {
	clk := clock.Real{}
	srv := New(st, cfg, catalogPath, clk)
	addr := cfg.Listen
	if addr == "" {
		addr = "127.0.0.1:8092"
	}
	fmt.Printf("riverbench listening on %s\n", addr)
	return http.ListenAndServe(addr, srv.Handler())
}
