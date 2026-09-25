package publisher

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/drain"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/journal"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/lifecycle"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/buffer"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/mountlink"
)

func BuildAtlas(bufferPath, dbPath, seed, scenario string) (model.AllocationAtlas, error) {
	snap, err := buffer.ReadSnapshot(bufferPath)
	if err != nil {
		return model.AllocationAtlas{}, err
	}
	db, err := journal.Open(dbPath)
	if err != nil {
		return model.AllocationAtlas{}, err
	}
	defer db.Close()
	runID, summary, placements, err := journal.LatestSummary(db, seed, scenario)
	if err != nil {
		return model.AllocationAtlas{}, err
	}
	drained, _ := drain.FilterEligible(snap.Allocations)
	active, _ := lifecycle.FilterStale(drained, snap.StaleCutoff)
	joins := mountlink.JoinMounts(active, snap.CSIVolumes)
	rep := model.AllocationAtlas{
		Seed:         seed,
		Scenario:     scenario,
		FocusAllocID: snap.FocusAllocID,
		RunID:        runID,
		VolumeJoins:  joins,
		Placements:   placements,
		Summary:      summary,
	}
	rep.AuditDigest = AuditDigest(summary, placements, joins)
	return rep, nil
}

func AuditDigest(summary model.SummaryBlock, placements []model.PlacementRow, joins []model.VolumeJoinRow) string {
	body := canonicalBody(summary, placements, joins)
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}

func canonicalBody(summary model.SummaryBlock, placements []model.PlacementRow, joins []model.VolumeJoinRow) string {
	keys := make([]string, 0, len(joins))
	for _, j := range joins {
		keys = append(keys, j.VolumeKey)
	}
	sort.Strings(keys)
	keysJSON, _ := json.Marshal(keys)
	ranks := make([]int, 0, len(placements))
	for _, p := range placements {
		ranks = append(ranks, p.PlacementRank)
	}
	ranksJSON, _ := json.Marshal(ranks)
	return fmt.Sprintf(
		`{"active_alloc_count":%d,"affinity_monotone_ok":%t,"constraint_pass_ok":%t,"drain_excluded":%d,"placement_ranks":%s,"reschedule_total":%d,"spread_penalty_total":%d,"stale_suppressed":%d,"volume_keys":%s}`,
		summary.ActiveAllocCount,
		summary.AffinityMonotoneOK,
		summary.ConstraintPassOK,
		summary.DrainExcluded,
		string(ranksJSON),
		summary.RescheduleTotal,
		summary.SpreadPenaltyTotal,
		summary.StaleSuppressed,
		string(keysJSON),
	)
}

func WriteAtlas(path string, rep model.AllocationAtlas) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
