package dedupe

import (
	"fmt"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Collapse(findings []model.Finding, ruleKeyFn func(model.Finding) string, remapFn func(string) string) []model.Finding {
	buckets := map[string][]model.Finding{}
	for _, f := range findings {
		rk := ruleKeyFn(f)
		uri := remapFn(f.URI)
		key := rk + "|" + uri + "|" + fmt.Sprintf("%d", f.StartLine)
		buckets[key] = append(buckets[key], f)
	}
	out := make([]model.Finding, 0, len(buckets))
	for _, group := range buckets {
		best := group[0]
		for _, cand := range group[1:] {
			if model.LevelRank(cand.Level) > model.LevelRank(best.Level) {
				best = cand
			} else if model.LevelRank(cand.Level) == model.LevelRank(best.Level) && cand.FindingID < best.FindingID {
				best = cand
			}
		}
		out = append(out, best)
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].FindingID < out[j].FindingID
	})
	return out
}
