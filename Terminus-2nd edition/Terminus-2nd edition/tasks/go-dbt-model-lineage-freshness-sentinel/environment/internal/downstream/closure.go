package downstream

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func Closure(exposures []model.ExposureNode, models []model.ModelNode) map[string][]string {
	modelSet := map[string]bool{}
	for _, m := range models {
		modelSet[m.UniqueID] = true
	}
	out := map[string][]string{}
	for _, e := range exposures {
		refs := []string{}
		for _, d := range e.DependsOn {
			if modelSet[d] {
				refs = append(refs, d)
			}
		}
		sort.Strings(refs)
		out[e.UniqueID] = refs
	}
	return out
}
