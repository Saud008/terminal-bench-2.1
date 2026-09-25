package runscan

import (
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packstate"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/downstream"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/enabledpolicy"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/graphorder"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/scanstore"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/sourcewindow"
)

type Input struct {
	Seed        string
	Pack        string
	StagingPath string
	DBPath      string
}

type Result struct {
	ScanID       int64
	ModelOrder   []string
	Freshness    []model.FreshnessStatus
	ExposureRefs map[string][]string
	Summary      model.ScanSummary
}

func ComputeFromSnapshot(snap model.StagingSnapshot) (Result, error) {
	order := graphorder.EnabledTopo(snap.Models)
	fresh, err := sourcewindow.EvaluateSources(snap.Sources, snap.EvaluatedAt)
	if err != nil {
		return Result{}, err
	}
	refs := downstream.Closure(snap.Exposures, snap.Models)
	stale := 0
	for _, f := range fresh {
		if f.Status != "ok" {
			stale++
		}
	}
	enabledCount := 0
	for _, m := range snap.Models {
		if m.Enabled {
			enabledCount++
		}
	}
	summary := model.ScanSummary{
		EnabledModelCount: enabledCount,
		StaleSourceCount:  stale,
		ExposureCount:     len(snap.Exposures),
		DisabledRefOK:     enabledpolicy.EnabledReferencesDisabled(snap.Models),
	}
	return Result{
		ModelOrder:   order,
		Freshness:    fresh,
		ExposureRefs: refs,
		Summary:      summary,
	}, nil
}

func RunScan(in Input) (Result, error) {
	snap, err := packstate.ReadSnapshot(in.StagingPath)
	if err != nil {
		return Result{}, err
	}
	if err := packstate.ValidateSeedBundle(snap, in.Seed, in.Pack); err != nil {
		return Result{}, err
	}
	res, err := ComputeFromSnapshot(snap)
	if err != nil {
		return Result{}, err
	}
	db, err := scanstore.Open(in.DBPath)
	if err != nil {
		return Result{}, err
	}
	defer db.Close()
	scanID, err := scanstore.InsertScan(db, in.Seed, in.Pack, res.Summary)
	if err != nil {
		return Result{}, err
	}
	res.ScanID = scanID
	return res, nil
}
