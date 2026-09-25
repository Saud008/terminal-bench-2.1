package dedupe

import (
	"fmt"
	"sort"

	"github.com/terminus/sarbctl-curator/internal/model"
)

type keyedFinding struct {
	RuleKey string
	URI     string
	Line    int
	Finding model.Finding
}

func Collapse(findings []model.Finding, ruleKeyFn func(model.Finding) string, remapFn func(string) string) []model.Finding {
	seen := map[string]model.Finding{}
	var order []string
	for _, f := range findings {
		rk := ruleKeyFn(f)
		uri := remapFn(f.URI)
		key := rk + "|" + uri + "|" + fmt.Sprintf("%d", f.StartLine)
		if _, ok := seen[key]; !ok {
			seen[key] = f
			order = append(order, key)
		}
	}
	out := make([]model.Finding, 0, len(order))
	for _, k := range order {
		out = append(out, seen[k])
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].FindingID < out[j].FindingID
	})
	return out
}
