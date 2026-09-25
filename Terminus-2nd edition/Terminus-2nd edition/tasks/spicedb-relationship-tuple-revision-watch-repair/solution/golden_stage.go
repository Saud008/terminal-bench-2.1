package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/example/spicedb-relation-watch/internal/caveat"
	"github.com/example/spicedb-relation-watch/internal/closure"
	"github.com/example/spicedb-relation-watch/internal/config"
	"github.com/example/spicedb-relation-watch/internal/model"
	"github.com/example/spicedb-relation-watch/internal/store"
)

// Stager writes revision snapshots after tuple mutations.
type Stager struct {
	cfg   *config.Config
	store *store.Store
}

// New creates an ingest stager.
func New(cfg *config.Config, st *store.Store) *Stager {
	return &Stager{cfg: cfg, store: st}
}

// WriteRevisionSnapshot persists /app/state/revision-snapshot.json after tuple writes.
func (s *Stager) WriteRevisionSnapshot(revision int64) error {
	tuples, err := s.store.ActiveTuplesAtRevision(revision)
	if err != nil {
		return err
	}
	namespaces, err := s.store.ListNamespaces(revision)
	if err != nil {
		return err
	}
	count, err := s.store.CountActiveTuples(revision)
	if err != nil {
		return err
	}

	cache := closure.New(s.store, 0)
	caveats := caveat.New()
	probes := []model.CheckSummary{
		{Namespace: "doc", Object: "plan", Relation: "viewer", Subject: "user:alice"},
		{Namespace: "doc", Object: "plan", Relation: "viewer", Subject: "user:bob"},
	}
	summaries := make([]model.CheckSummary, 0, len(probes))
	for _, probe := range probes {
		allowed, err := evaluateProbe(cache, caveats, s.store, revision, probe)
		if err != nil {
			return err
		}
		probe.Allowed = allowed
		summaries = append(summaries, probe)
	}

	snap := model.RevisionSnapshot{
		Revision:       revision,
		TupleCount:     count,
		Namespaces:     namespaces,
		Tuples:         make([]model.SnapshotTuple, 0, len(tuples)),
		CheckSummaries: summaries,
	}
	for _, t := range tuples {
		st := model.SnapshotTuple{
			Namespace:  t.Namespace,
			Object:     t.Object,
			Relation:   t.Relation,
			Subject:    t.Subject,
			CaveatExpr: t.CaveatExpr,
			Active:     true,
		}
		snap.Tuples = append(snap.Tuples, st)
	}

	if err := os.MkdirAll(filepath.Dir(s.cfg.SnapshotPath), 0o755); err != nil {
		return fmt.Errorf("mkdir snapshot dir: %w", err)
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	if err := os.WriteFile(s.cfg.SnapshotPath, raw, 0o644); err != nil {
		return fmt.Errorf("write snapshot: %w", err)
	}
	return nil
}

func evaluateProbe(
	cache *closure.Cache,
	caveats *caveat.Evaluator,
	st *store.Store,
	revision int64,
	probe model.CheckSummary,
) (bool, error) {
	ok, err := cache.HasTransitivePermission(revision, probe.Namespace, probe.Object, probe.Relation, probe.Subject)
	if err != nil {
		return false, err
	}
	if !ok {
		return false, nil
	}
	meta, err := st.DirectTupleLookup(revision, probe.Namespace, probe.Object, probe.Relation, probe.Subject)
	if err != nil {
		return false, err
	}
	if meta == nil {
		return ok, nil
	}
	return caveats.Passes(&meta.Tuple, probe.Subject, meta.TombstoneRevision, revision), nil
}

// LoadRevisionSnapshot reads the on-disk snapshot if present.
func (s *Stager) LoadRevisionSnapshot() (*model.RevisionSnapshot, error) {
	raw, err := os.ReadFile(s.cfg.SnapshotPath)
	if err != nil {
		return nil, err
	}
	var snap model.RevisionSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return nil, err
	}
	return &snap, nil
}
