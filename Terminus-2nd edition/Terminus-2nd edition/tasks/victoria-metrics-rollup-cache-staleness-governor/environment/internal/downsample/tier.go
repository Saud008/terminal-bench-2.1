package downsample

import "github.com/chronostack/metricrollup/internal/model"

// ApplyTiers copies raw rollups to configured downsample tiers.
func ApplyTiers(raw model.SeriesRollup, tiers []string) []model.SeriesRollup {
	out := []model.SeriesRollup{}
	for _, tier := range tiers {
		cp := raw
		cp.Tier = tier
		if tier != "raw" {
			cp.Stale = false
		}
		out = append(out, cp)
	}
	return out
}
