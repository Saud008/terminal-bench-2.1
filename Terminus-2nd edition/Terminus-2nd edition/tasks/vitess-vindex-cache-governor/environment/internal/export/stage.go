package export

import (
	"encoding/json"
	"os"

	"vtgatesim/internal/model"
	"vtgatesim/internal/staging"
)

func BuildAudit(snapshotPath string, plan model.RoutePlan) (model.RoutingAudit, error) {
	snap, err := staging.ReadSnapshot(snapshotPath)
	if err != nil {
		return model.RoutingAudit{}, err
	}
	counts := map[string]int{}
	for _, r := range plan.Routes {
		counts[r.Shard]++
	}
	scatterFailures := 0
	if !plan.ScatterOK {
		scatterFailures = 1
	}
	return model.RoutingAudit{
		Generation:      snap.Generation,
		SnapshotPath:    snapshotPath,
		RouteCount:      len(plan.Routes),
		CacheHitCount:   plan.CacheHits,
		CoalesceDropped: snap.CoalesceDropped,
		ScatterFailures: scatterFailures,
		ShardCounts:     counts,
	}, nil
}

func WriteAudit(path string, audit model.RoutingAudit) error {
	data, err := json.MarshalIndent(audit, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}
