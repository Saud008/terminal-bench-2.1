package compiler

import (
	"fmt"
	"os"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/bundleloader"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/buffer"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/drain"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/journal"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/lifecycle"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/mountlink"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/placement"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/spread"
)

type Input struct {
	Seed       string
	Scenario   string
	BufferPath string
	DBPath     string
}

type Result struct {
	RunID       int64
	VolumeJoins []model.VolumeJoinRow
	Placements  []model.PlacementRow
	Summary     model.SummaryBlock
}

func nodePoolFromEnv() string {
	if p := os.Getenv("TB3_NODE_POOL"); p != "" {
		return p
	}
	return "default"
}

func affinityMonotone(placements []model.PlacementRow) bool {
	for i := 1; i < len(placements); i++ {
		if placements[i].PlacementRank < placements[i-1].PlacementRank {
			return false
		}
		if placements[i].AffinityScore > placements[i-1].AffinityScore {
			return false
		}
	}
	return true
}

func RunCompile(in Input) (Result, error) {
	snap, err := buffer.ReadSnapshot(in.BufferPath)
	if err != nil {
		return Result{}, err
	}
	if err := buffer.ValidateSeedScenario(snap, in.Seed, in.Scenario); err != nil {
		return Result{}, err
	}
	drained, drainExcluded := drain.FilterEligible(snap.Allocations)
	active, suppressed := lifecycle.FilterStale(drained, snap.StaleCutoff)
	reschedule := lifecycle.RescheduleTotal(active)
	joins := mountlink.JoinMounts(active, snap.CSIVolumes)
	placements := placement.RankPlacements(active, nodePoolFromEnv())
	constraintOK := placement.ConstraintPass(active)
	summary := model.SummaryBlock{
		ActiveAllocCount:   len(active),
		StaleSuppressed:    suppressed,
		DrainExcluded:      drainExcluded,
		RescheduleTotal:    reschedule,
		VolumeJoinCount:    len(joins),
		SpreadPenaltyTotal: spread.PenaltyTotal(active),
		ConstraintPassOK:   constraintOK,
		AffinityMonotoneOK: affinityMonotone(placements),
	}
	db, err := journal.Open(in.DBPath)
	if err != nil {
		return Result{}, err
	}
	defer db.Close()
	runID, err := journal.ReplaceRun(db, in.Seed, in.Scenario, snap.FocusAllocID, snap.LoadSeq, summary, placements)
	if err != nil {
		return Result{}, err
	}
	_, ok := bundleloader.FindAlloc(snap.Allocations, snap.FocusAllocID)
	if !ok {
		return Result{}, fmt.Errorf("focus alloc missing")
	}
	return Result{
		RunID:       runID,
		VolumeJoins: joins,
		Placements:  placements,
		Summary:     summary,
	}, nil
}
