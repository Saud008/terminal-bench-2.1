package graphorder

import (
	"sort"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
)

func EnabledTopo(models []model.ModelNode) []string {
	byID := map[string]model.ModelNode{}
	for _, m := range models {
		byID[m.UniqueID] = m
	}
	visited := map[string]bool{}
	out := []string{}
	var visit func(string)
	visit = func(id string) {
		if visited[id] {
			return
		}
		visited[id] = true
		m, ok := byID[id]
		if !ok {
			return
		}
		for _, d := range m.DependsOn {
			visit(d)
		}
		out = append(out, id)
	}
	ids := make([]string, 0, len(models))
	for _, m := range models {
		ids = append(ids, m.UniqueID)
	}
	sort.Strings(ids)
	for _, id := range ids {
		visit(id)
	}
	return out
}
