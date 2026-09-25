package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/example/spicedb-relation-watch/internal/caveat"
	"github.com/example/spicedb-relation-watch/internal/closure"
	"github.com/example/spicedb-relation-watch/internal/config"
	"github.com/example/spicedb-relation-watch/internal/ingest"
	"github.com/example/spicedb-relation-watch/internal/model"
	"github.com/example/spicedb-relation-watch/internal/store"
	"github.com/example/spicedb-relation-watch/internal/token"
)

// Publisher builds /app/output/authz-report.json from the revision snapshot.
type Publisher struct {
	cfg     *config.Config
	store   *store.Store
	stager  *ingest.Stager
	cache   *closure.Cache
	caveats *caveat.Evaluator
}

// New creates an export publisher.
func New(cfg *config.Config, st *store.Store, stager *ingest.Stager, cache *closure.Cache) *Publisher {
	return &Publisher{
		cfg:     cfg,
		store:   st,
		stager:  stager,
		cache:   cache,
		caveats: caveat.New(),
	}
}

// PublishAuthzReport writes authz-report.json using snapshot revision as source of truth.
func (p *Publisher) PublishAuthzReport() (*model.AuthzReport, error) {
	snap, err := p.stager.LoadRevisionSnapshot()
	if err != nil {
		return nil, fmt.Errorf("load snapshot: %w", err)
	}
	head, err := p.store.CurrentRevision()
	if err != nil {
		return nil, err
	}

	report := model.AuthzReport{
		GeneratedRevision: head,
		SnapshotRevision:  snap.Revision,
		NamespaceCounts:   map[string]int{},
		TupleTotal:        snap.TupleCount,
	}
	for _, ns := range snap.Namespaces {
		report.NamespaceCounts[ns] = 0
	}
	for _, t := range snap.Tuples {
		if t.Active {
			report.NamespaceCounts[t.Namespace]++
		}
	}

	probes := []model.CheckSummary{
		{Namespace: "doc", Object: "plan", Relation: "viewer", Subject: "user:alice"},
		{Namespace: "doc", Object: "plan", Relation: "viewer", Subject: "user:bob"},
	}
	for _, probe := range probes {
		allowed, err := p.evaluate(probe, snap.Revision)
		if err != nil {
			return nil, err
		}
		probe.Allowed = allowed
		if allowed {
			report.AllowedChecks = append(report.AllowedChecks, probe)
		} else {
			report.DeniedChecks = append(report.DeniedChecks, probe)
		}
	}

	if err := os.MkdirAll(filepath.Dir(p.cfg.ExportPath), 0o755); err != nil {
		return nil, err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return nil, err
	}
	raw = append(raw, '\n')
	if err := os.WriteFile(p.cfg.ExportPath, raw, 0o644); err != nil {
		return nil, err
	}
	_ = token.EncodeRevision(snap.Revision)
	return &report, nil
}

func (p *Publisher) evaluate(probe model.CheckSummary, revision int64) (bool, error) {
	ok, err := p.cache.HasTransitivePermission(revision, probe.Namespace, probe.Object, probe.Relation, probe.Subject)
	if err != nil {
		return false, err
	}
	if !ok {
		return false, nil
	}
	meta, err := p.store.DirectTupleLookup(revision, probe.Namespace, probe.Object, probe.Relation, probe.Subject)
	if err != nil {
		return false, err
	}
	if meta == nil {
		return ok, nil
	}
	return p.caveats.Passes(&meta.Tuple, probe.Subject, meta.TombstoneRevision, revision), nil
}
