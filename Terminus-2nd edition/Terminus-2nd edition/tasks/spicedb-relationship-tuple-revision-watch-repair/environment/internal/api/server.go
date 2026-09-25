package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/example/spicedb-relation-watch/internal/caveat"
	"github.com/example/spicedb-relation-watch/internal/check"
	"github.com/example/spicedb-relation-watch/internal/closure"
	"github.com/example/spicedb-relation-watch/internal/config"
	"github.com/example/spicedb-relation-watch/internal/export"
	"github.com/example/spicedb-relation-watch/internal/ingest"
	"github.com/example/spicedb-relation-watch/internal/model"
	"github.com/example/spicedb-relation-watch/internal/revision"
	"github.com/example/spicedb-relation-watch/internal/store"
	"github.com/example/spicedb-relation-watch/internal/token"
	"github.com/example/spicedb-relation-watch/internal/watch"
)

// Server exposes the relation watch HTTP API.
type Server struct {
	cfg      *config.Config
	store    *store.Store
	log      *revision.Log
	stager   *ingest.Stager
	publish  *export.Publisher
	cache    *closure.Cache
	caveats  *caveat.Evaluator
	snapshot *check.SnapshotPolicy
}

// New wires HTTP handlers.
func New(cfg *config.Config, st *store.Store) *Server {
	cache := closure.New(st, cfg.ClosureCacheSize)
	stager := ingest.New(cfg, st)
	return &Server{
		cfg:      cfg,
		store:    st,
		log:      revision.New(st),
		stager:   stager,
		publish:  export.New(cfg, st, stager, cache),
		cache:    cache,
		caveats:  caveat.New(),
		snapshot: check.NewSnapshotPolicy(cfg.WatchStaleLagThreshold),
	}
}

// Handler returns the mux for protected routes.
func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/v1/admin/seed", s.handleSeed)
	mux.HandleFunc("/v1/tuple/write", s.handleTupleWrite)
	mux.HandleFunc("/v1/check", s.handleCheck)
	mux.HandleFunc("/v1/watch", s.handleWatch)
	mux.HandleFunc("/v1/export", s.handleExport)
	mux.HandleFunc("/v1/admin/delete-namespace-prefix", s.handleDeletePrefix)
	return mux
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	_ = enc.Encode(v)
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	rev, err := s.store.CurrentRevision()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]any{"status": "ok", "revision": rev})
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
	name := req.Fixture
	if name == "" {
		name = "tuples/base"
	}
	path := filepath.Join(s.cfg.FixtureDir, name+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var tuples []model.TupleWriteRequest
	if err := json.Unmarshal(raw, &tuples); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var last int64
	for _, tw := range tuples {
		t := model.Tuple{
			Namespace:  tw.Namespace,
			Object:     tw.Object,
			Relation:   tw.Relation,
			Subject:    tw.Subject,
			CaveatExpr: tw.CaveatExpr,
		}
		op := tw.Operation
		if op == "" {
			op = "TOUCH"
		}
		rev, err := s.store.WriteTuple(op, t)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		last = rev
	}
	if err := s.stager.WriteRevisionSnapshot(last); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]any{"revision": last, "seeded": len(tuples)})
}

func (s *Server) handleTupleWrite(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.TupleWriteRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if req.Namespace == "" || req.Object == "" || req.Relation == "" || req.Subject == "" {
		http.Error(w, "missing tuple fields", http.StatusBadRequest)
		return
	}
	op := req.Operation
	if op == "" {
		op = "TOUCH"
	}
	t := model.Tuple{
		Namespace:  req.Namespace,
		Object:     req.Object,
		Relation:   req.Relation,
		Subject:    req.Subject,
		CaveatExpr: req.CaveatExpr,
	}
	rev, err := s.store.WriteTuple(op, t)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := s.stager.WriteRevisionSnapshot(rev); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]any{"revision": rev, "zed_token": token.EncodeRevision(rev)})
}

func (s *Server) handleDeletePrefix(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var body struct {
		Prefix string `json:"prefix"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	if body.Prefix == "" {
		http.Error(w, "prefix required", http.StatusBadRequest)
		return
	}
	rev, affected, err := s.store.DeleteNamespacePrefix(body.Prefix)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	s.cache.InvalidateNamespacePrefix(body.Prefix)
	if err := s.stager.WriteRevisionSnapshot(rev); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]any{"revision": rev, "deleted": affected})
}

func (s *Server) handleCheck(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.CheckRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	atRevision, err := token.DecodeRevision(req.ZedToken)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	head, err := s.store.CurrentRevision()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	usedStale := s.snapshot.ShouldUseStale(head, atRevision)

	var allowed bool
	if usedStale {
		snap, err := s.stager.LoadRevisionSnapshot()
		if err == nil {
			for _, summary := range snap.CheckSummaries {
				if summary.Namespace == req.Namespace && summary.Object == req.Object &&
					summary.Relation == req.Relation && summary.Subject == req.Subject {
					allowed = summary.Allowed
					break
				}
			}
		}
	} else {
		allowed, err = s.evaluatePermission(atRevision, req.Namespace, req.Object, req.Relation, req.Subject)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	writeJSON(w, model.CheckResponse{
		Allowed:      allowed,
		Revision:     head,
		ZedToken:     token.EncodeRevision(head),
		UsedStale:    usedStale,
	})
}

func (s *Server) evaluatePermission(revision int64, ns, obj, rel, subj string) (bool, error) {
	ok, err := s.cache.HasTransitivePermission(revision, ns, obj, rel, subj)
	if err != nil {
		return false, err
	}
	if !ok {
		return false, nil
	}
	meta, err := s.store.DirectTupleLookup(revision, ns, obj, rel, subj)
	if err != nil {
		return false, err
	}
	if meta == nil {
		return ok, nil
	}
	return s.caveats.Passes(&meta.Tuple, subj, meta.TombstoneRevision, revision), nil
}

func (s *Server) handleWatch(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req model.WatchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad json", http.StatusBadRequest)
		return
	}
	limit := req.Limit
	if limit <= 0 {
		limit = 50
	}
	events, err := s.log.EventsAfter(req.AfterRevision, limit*2)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	cur := watch.NewCursor(req.AfterRevision)
	delivered, skipped := cur.FilterAndAdvance(events, req.NamespaceFilter)
	if len(delivered) > limit {
		delivered = delivered[:limit]
	}
	writeJSON(w, model.WatchResponse{
		Events:        delivered,
		NextCursor:    cur.Position,
		FilteredSkips: skipped,
	})
}

func (s *Server) handleExport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	report, err := s.publish.PublishAuthzReport()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, model.ExportResponse{
		Path:     s.cfg.ExportPath,
		Revision: report.SnapshotRevision,
		Checks:   len(report.AllowedChecks) + len(report.DeniedChecks),
	})
}

// ResetState clears runtime dirs for tests.
func ResetState(cfg *config.Config) error {
	for _, dir := range []string{"/app/output", "/app/state", "/app/data"} {
		if err := os.RemoveAll(dir); err != nil {
			return err
		}
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	if cfg != nil && cfg.DBPath != "" {
		_ = os.Remove(cfg.DBPath)
	}
	return nil
}

// SeedFixturePath resolves fixture file path.
func SeedFixturePath(cfg *config.Config, name string) string {
	if !strings.HasSuffix(name, ".json") {
		name += ".json"
	}
	return filepath.Join(cfg.FixtureDir, name)
}

// EnsureDirs creates output/state/data directories.
func EnsureDirs(cfg *config.Config) error {
	for _, p := range []string{filepath.Dir(cfg.DBPath), filepath.Dir(cfg.SnapshotPath), filepath.Dir(cfg.ExportPath)} {
		if err := os.MkdirAll(p, 0o755); err != nil {
			return fmt.Errorf("mkdir %s: %w", p, err)
		}
	}
	return nil
}
