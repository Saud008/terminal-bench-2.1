package curate

import (
	"fmt"

	"github.com/terminus/mlflow-provenance-curator/internal/dataset"
	"github.com/terminus/mlflow-provenance-curator/internal/digest"
	"github.com/terminus/mlflow-provenance-curator/internal/ingest"
	"github.com/terminus/mlflow-provenance-curator/internal/ledger"
	"github.com/terminus/mlflow-provenance-curator/internal/lineage"
	"github.com/terminus/mlflow-provenance-curator/internal/metrics"
	"github.com/terminus/mlflow-provenance-curator/internal/model"
	"github.com/terminus/mlflow-provenance-curator/internal/staging"
)

type Input struct {
	Seed        string
	Scenario    string
	StagingPath string
	DBPath      string
}

type Result struct {
	RunID           int64
	LineageChain    []string
	ArtifactDigests []model.ArtifactDigest
	MetricEpochs    []model.MetricPoint
	DatasetBindings []model.DatasetBinding
	Summary         model.SummaryBlock
}

func RunBind(in Input) (Result, error) {
	snap, err := staging.ReadSnapshot(in.StagingPath)
	if err != nil {
		return Result{}, err
	}
	if err := staging.ValidateSeedScenario(snap, in.Seed, in.Scenario); err != nil {
		return Result{}, err
	}
	focus, ok := ingest.FindRun(snap.Runs, snap.FocusRunID)
	if !ok {
		return Result{}, fmt.Errorf("focus run missing")
	}
	chain := lineage.Closure(snap.Runs, snap.FocusRunID)
	ordered := metrics.OrderMetrics(focus.Metrics)
	bindings, bindingOK := dataset.BindFocusRun(focus, snap.DatasetManifests)
	artifacts := digest.CollectFocusArtifacts(focus)
	summary := model.SummaryBlock{
		BindingOK:        bindingOK,
		EpochMonotonicOK: metrics.EpochMonotonicOK(ordered),
		LineageDepth:     len(chain),
		ArtifactCount:    len(artifacts),
	}
	db, err := ledger.Open(in.DBPath)
	if err != nil {
		return Result{}, err
	}
	defer db.Close()
	runID, err := ledger.ReplaceRun(db, in.Seed, in.Scenario, snap.FocusRunID, snap.IngestSeq, summary, chain)
	if err != nil {
		return Result{}, err
	}
	return Result{
		RunID:           runID,
		LineageChain:    chain,
		ArtifactDigests: artifacts,
		MetricEpochs:    ordered,
		DatasetBindings: bindings,
		Summary:         summary,
	}, nil
}
