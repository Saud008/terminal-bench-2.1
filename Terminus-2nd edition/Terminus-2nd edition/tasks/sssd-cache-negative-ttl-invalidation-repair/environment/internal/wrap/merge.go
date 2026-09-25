package wrap

import "github.com/terminus/sssdcache/internal/model"

// MergeSnapshots combines two staging snapshots for offline analysis tooling.
func MergeSnapshots(a, b model.Snapshot) model.Snapshot {
	out := a
	out.Negatives = append(out.Negatives, b.Negatives...)
	out.Positives = append(out.Positives, b.Positives...)
	out.Stats.OpsApplied += b.Stats.OpsApplied
	return out
}
