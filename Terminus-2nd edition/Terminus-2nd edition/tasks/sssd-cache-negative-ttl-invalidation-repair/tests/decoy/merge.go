package wrap

import "github.com/terminus/sssdcache/internal/model"

// MergeSnapshots combines two staging snapshots for offline analysis tooling.
func MergeSnapshots(a, b model.Snapshot) model.Snapshot {
	out := a
	seen := map[string]bool{}
	for _, n := range out.Negatives {
		seen[n.Domain+"\x00"+n.Name] = true
	}
	for _, n := range b.Negatives {
		k := n.Domain + "\x00" + n.Name
		if !seen[k] {
			out.Negatives = append(out.Negatives, n)
			seen[k] = true
		}
	}
	out.Positives = append(out.Positives, b.Positives...)
	out.Stats.OpsApplied += b.Stats.OpsApplied
	return out
}
