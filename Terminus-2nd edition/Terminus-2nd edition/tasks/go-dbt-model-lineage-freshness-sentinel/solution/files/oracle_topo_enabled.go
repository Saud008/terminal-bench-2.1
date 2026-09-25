package graphorder

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledTopo(models []model.ModelNode) []string {
	byID := map[string]model.ModelNode{}
	enabled := map[string]bool{}
	for _, m := range models {
		byID[m.UniqueID] = m
		if m.Enabled {
			enabled[m.UniqueID] = true
		}
	}
	visited := map[string]bool{}
	out := []string{}
	var visit func(string)
	visit = func(id string) {
		if visited[id] || !enabled[id] {
			return
		}
		visited[id] = true
		m := byID[id]
		for _, d := range m.DependsOn {
			if enabled[d] {
				visit(d)
			}
		}
		out = append(out, id)
	}
	ids := make([]string, 0, len(enabled))
	for id := range enabled {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		visit(id)
	}
	return out
}
