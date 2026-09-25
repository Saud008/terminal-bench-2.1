package export

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

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
	rep.AuditDigest = AuditDigest(summary, chain, snap.DatasetManifests)
	return rep, nil
}

func AuditDigest(summary model.SummaryBlock, chain []string, manifests map[string]model.DatasetManifest) string {
	body := canonicalSummary(summary, chain, manifests)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func canonicalSummary(summary model.SummaryBlock, chain []string, manifests map[string]model.DatasetManifest) string {
	hashes := make([]string, 0, len(manifests))
	for _, m := range manifests {
		h := m.VersionHash
		if s := dataset.ManifestSalt(); s != "" {
			h = h + s
		}
		hashes = append(hashes, h)
	}
	sort.Strings(hashes)
	chainJSON, _ := json.Marshal(chain)
	hashJSON, _ := json.Marshal(hashes)
	return fmt.Sprintf(
		`{"artifact_count":%d,"binding_ok":%t,"epoch_monotonic_ok":%t,"lineage_depth":%d,"lineage_chain":%s,"version_hashes":%s}`,
		summary.ArtifactCount,
		summary.BindingOK,
		summary.EpochMonotonicOK,
		summary.LineageDepth,
		string(chainJSON),
		string(hashJSON),
	)
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
	snap, err := staging.ReadSnapshot(stagingPath)
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	res, err := curate.RunBind(curate.Input{
		Seed: seed, Scenario: scenario, StagingPath: stagingPath, DBPath: dbPath,
	})
	if err != nil {
		return model.ProvenanceReport{}, err
	}
	rep := model.ProvenanceReport{
		Seed:            seed,
		Scenario:        scenario,
		FocusRunID:      snap.FocusRunID,
		RunID:           res.RunID,
		LineageChain:    res.LineageChain,
		ArtifactDigests: res.ArtifactDigests,
		MetricEpochs:    res.MetricEpochs,
		DatasetBindings: res.DatasetBindings,
		Summary:         res.Summary,
	}
	rep.AuditDigest = AuditDigest(res.Summary, res.LineageChain, snap.DatasetManifests)
	return rep, nil
}
