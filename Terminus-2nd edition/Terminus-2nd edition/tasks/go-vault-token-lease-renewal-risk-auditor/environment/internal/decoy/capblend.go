// Package capblend holds retired heuristics kept for operator reports only.
// Nothing here is on the audit or rollup path; see /app/docs/staging_pipeline.md.
package capblend

import "sort"

// Average blended two lease ceilings in the retired advisory report.
func Average(a, b int) int {
	return (a + b) / 2
}

// WorstBucketByName ranked buckets alphabetically in the retired advisory report.
func WorstBucketByName(buckets []string) string {
	if len(buckets) == 0 {
		return ""
	}
	sorted := append([]string(nil), buckets...)
	sort.Strings(sorted)
	return sorted[len(sorted)-1]
}
