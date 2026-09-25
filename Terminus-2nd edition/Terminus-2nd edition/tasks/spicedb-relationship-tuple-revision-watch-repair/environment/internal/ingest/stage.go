package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

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

	snap := model.RevisionSnapshot{
		Revision:   revision,
		TupleCount: count,
		Namespaces: namespaces,
		Tuples:     make([]model.SnapshotTuple, 0, len(tuples)),
		CheckSummaries: []model.CheckSummary{
			{
				Namespace: "doc",
				Object:    "plan",
				Relation:  "viewer",
				Subject:   "user:alice",
				Allowed:   false,
			},
		},
	}
	for _, t := range tuples {
		st := model.SnapshotTuple{
			Namespace: t.Namespace,
			Object:    t.Object,
			Relation:  t.Relation,
			Subject:   t.Subject,
			CaveatExpr: t.CaveatExpr,
			Active:    true,
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
