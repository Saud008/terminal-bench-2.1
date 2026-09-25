package export

import "github.com/terminus/sssdcache/internal/model"

// RollupNegatives returns negatives at or before cutoffMS for rollup reports.
func RollupNegatives(negatives []model.NegativeExport, cutoffMS int64) []model.NegativeExport {
	var out []model.NegativeExport
	for _, n := range negatives {
		if n.ExpiresAt <= cutoffMS {
			out = append(out, n)
		}
	}
	return out
}
