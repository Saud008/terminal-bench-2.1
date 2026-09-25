package downstream

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func Closure(exposures []model.ExposureNode, models []model.ModelNode) map[string][]string {
	modelSet := map[string]model.ModelNode{}
	for _, m := range models {
		modelSet[m.UniqueID] = m
	}
	var collect func(string, map[string]bool)
	collect = func(id string, seen map[string]bool) {
		if seen[id] {
			return
		}
		m, ok := modelSet[id]
		if !ok {
			return
		}
		seen[id] = true
		for _, d := range m.DependsOn {
			collect(d, seen)
		}
	}
	out := map[string][]string{}
	for _, e := range exposures {
		seen := map[string]bool{}
		for _, d := range e.DependsOn {
			collect(d, seen)
		}
		refs := make([]string, 0, len(seen))
		for id := range seen {
			refs = append(refs, id)
		}
		sort.Strings(refs)
		out[e.UniqueID] = refs
	}
	return out
}
