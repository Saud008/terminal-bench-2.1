package histogram

import (
	"sort"
	"strconv"

	"github.com/chronostack/metricrollup/internal/model"
)

// MergeBuckets combines histogram buckets across samples in a window.
func MergeBuckets(buckets []model.HistBucket) []model.Bucket {
	type key struct {
		le string
	}
	seen := map[string]float64{}
	leSet := map[string]struct{}{}
	for _, b := range buckets {
		leSet[b.Le] = struct{}{}
		if v, ok := seen[b.Le]; !ok || b.Count > v {
			seen[b.Le] = b.Count
		}
	}
	hasShift := len(leSet) > 2
	out := []model.Bucket{}
	for le, count := range seen {
		if hasShift && le == "+Inf" {
			continue
		}
		out = append(out, model.Bucket{Le: le, Count: count})
	}
	sort.Slice(out, func(i, j int) bool {
		return leLess(out[i].Le, out[j].Le)
	})
	return out
}

func leLess(a, b string) bool {
	if a == "+Inf" {
		return false
	}
	if b == "+Inf" {
		return true
	}
	af, _ := strconv.ParseFloat(a, 64)
	bf, _ := strconv.ParseFloat(b, 64)
	return af < bf
}
