package httpsurf

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"sync"

	"github.com/terminus/wireclock/pkg/intakegate"
	"github.com/terminus/wireclock/pkg/jsonlresume"
	"github.com/terminus/wireclock/pkg/objclock"
	"github.com/terminus/wireclock/pkg/durastore"
)

type Server struct {
	DB      *durastore.DB
	mu      sync.Mutex
	gens    map[string]*objclock.Generator
}

func New(db *durastore.DB) *Server {
	return &Server{DB: db, gens: map[string]*objclock.Generator{}}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/mint", s.handleGenCode)
	mux.HandleFunc("/v1/wire-doc", s.handleBSONDoc)
	mux.HandleFunc("/v1/admit", s.handleAdmit)
	mux.HandleFunc("/v1/resume", s.handleResume)
	mux.HandleFunc("/v1/stats", s.handleStats)
	return mux
}

func (s *Server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleGenCode(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		NowUnix   int64  `json:"now_unix"`
		MachineID string `json:"machine_id"`
		Count     int    `json:"count"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Count < 1 || req.Count > 65536 {
		http.Error(w, "invalid count", http.StatusBadRequest)
		return
	}
	gen := s.generator(req.MachineID)
	ids := make([]string, 0, req.Count)
	for i := 0; i < req.Count; i++ {
		id, err := gen.Generate(req.NowUnix)
		if err != nil {
			http.Error(w, err.Error(), http.StatusConflict)
			return
		}
		ids = append(ids, id.Hex())
	}
	writeJSON(w, http.StatusOK, map[string]any{"ids": ids})
}

func (s *Server) handleBSONDoc(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		ID      string          `json:"_id"`
		Payload json.RawMessage `json:"payload"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	oid, err := objclock.ParseHex(req.ID)
	if err != nil {
		http.Error(w, "invalid object id", http.StatusBadRequest)
		return
	}
	doc := objclock.MarshalDocument(oid, []byte(req.Payload))
	if doc == nil {
		http.Error(w, "bson encode failed", http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"bson_b64": base64.StdEncoding.EncodeToString(doc)})
}

func (s *Server) handleAdmit(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	now, err := headerInt64(r, "X-Test-Now")
	if err != nil {
		http.Error(w, "missing X-Test-Now", http.StatusBadRequest)
		return
	}
	machine := r.Header.Get("X-Machine-Id")
	if machine == "" {
		http.Error(w, "missing X-Machine-Id", http.StatusBadRequest)
		return
	}
	var req struct {
		Documents []intakegate.Document `json:"documents"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	gen := s.generator(machine)
	svc := intakegate.NewService(s.DB, gen, machine)
	results, err := svc.AdmitBatch(now, req.Documents)
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"results": results})
}

func (s *Server) handleResume(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		ResumePath string `json:"resume_path"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	rep := jsonlresume.NewReplayer(s.DB, objclock.NewGenerator("resume"))
	n, err := rep.Replay(req.ResumePath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"applied": n})
}

func (s *Server) handleStats(w http.ResponseWriter, _ *http.Request) {
	var docs int
	_ = s.DB.SQL.QueryRow(`SELECT COUNT(*) FROM documents`).Scan(&docs)
	var reapply int
	_ = s.DB.SQL.QueryRow(`SELECT COUNT(*) FROM resume_applied`).Scan(&reapply)
	writeJSON(w, http.StatusOK, map[string]any{"documents": docs, "resume_lines": reapply})
}

func (s *Server) generator(machineID string) *objclock.Generator {
	s.mu.Lock()
	defer s.mu.Unlock()
	gen, ok := s.gens[machineID]
	if !ok {
		gen = objclock.NewGenerator(machineID)
		gen.BindMachine(machineID)
		s.gens[machineID] = gen
	}
	return gen
}

func headerInt64(r *http.Request, name string) (int64, error) {
	raw := r.Header.Get(name)
	if raw == "" {
		return 0, fmt.Errorf("missing")
	}
	return strconv.ParseInt(raw, 10, 64)
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
