// Package export publishes eval summary certificates with audit_digest closure.
package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/mlflow-provenance-curator/internal/curate"
	"github.com/terminus/mlflow-provenance-curator/internal/dataset"
	"github.com/terminus/mlflow-provenance-curator/internal/digest"
	"github.com/terminus/mlflow-provenance-curator/internal/ingest"
	"github.com/terminus/mlflow-provenance-curator/internal/ledger"
	"github.com/terminus/mlflow-provenance-curator/internal/metrics"
	"github.com/terminus/mlflow-provenance-curator/internal/model"
	"github.com/terminus/mlflow-provenance-curator/internal/staging"
)

func BuildReport(stagingPath, dbPath, seed, scenario string) (model.ProvenanceReport, error) {
	snap, err := staging.ReadSnapshot(stagingPath)
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	db, err := ledger.Open(dbPath)
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	defer db.Close()
	runID, summary, chain, err := ledger.LatestSummary(db, seed, scenario)
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	focus, ok := ingest.FindRun(snap.Runs, snap.FocusRunID)
	if !ok {
		return model.ProvenanceReport{}, fmt.Errorf("focus run missing")
	}
	artifacts := digest.CollectFocusArtifacts(focus)
	ordered := metrics.OrderMetrics(focus.Metrics)
	bindings, _ := dataset.BindFocusRun(focus, snap.DatasetManifests)
	rep := model.ProvenanceReport{
		Seed:            seed,
		Scenario:        scenario,
		FocusRunID:      snap.FocusRunID,
		RunID:           runID,
		LineageChain:    chain,
		ArtifactDigests: artifacts,
		MetricEpochs:    ordered,
		DatasetBindings: bindings,
		Summary:         summary,
	}
	rep.AuditDigest = AuditDigest(summary)
	return rep, nil
}

func AuditDigest(summary model.SummaryBlock) string {
	body := fmt.Sprintf(
		`{"artifact_count":%d,"binding_ok":%t,"epoch_monotonic_ok":%t,"lineage_depth":%d}`,
		summary.ArtifactCount, summary.BindingOK, summary.EpochMonotonicOK, summary.LineageDepth,
	)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func WriteReport(path string, rep model.ProvenanceReport) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}

func BuildFromCurate(stagingPath, dbPath, seed, scenario string) (model.ProvenanceReport, error) {
	res, err := curate.RunBind(curate.Input{
		Seed: seed, Scenario: scenario, StagingPath: stagingPath, DBPath: dbPath,
	})
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	rep := model.ProvenanceReport{
		Seed:            seed,
		Scenario:        scenario,
		FocusRunID:      "",
		RunID:           res.RunID,
		LineageChain:    res.LineageChain,
		ArtifactDigests: res.ArtifactDigests,
		MetricEpochs:    res.MetricEpochs,
		DatasetBindings: res.DatasetBindings,
		Summary:         res.Summary,
	}
	rep.AuditDigest = AuditDigest(res.Summary)
	return rep, nil
}
