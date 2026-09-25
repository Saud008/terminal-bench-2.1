package amendlemma

import "github.com/terminus/airclos/internal/labtypes"

// CloseSeries reduces NOTAM rows to one row per series_id per amendment-closure-lemma.md.
func CloseSeries(notams []labtypes.NotamRecord) []labtypes.NotamRecord {
	seen := map[string]bool{}
	var out []labtypes.NotamRecord
	for _, n := range notams {
		if seen[n.SeriesID] {
			continue
		}
		seen[n.SeriesID] = true
		out = append(out, n)
	}
	return out
}
