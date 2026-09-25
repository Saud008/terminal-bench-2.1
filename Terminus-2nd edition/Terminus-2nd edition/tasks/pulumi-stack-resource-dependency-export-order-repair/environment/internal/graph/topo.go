package graph

import (
	"sort"

	"github.com/terminus/pulumi-dep-export/internal/model"
)

func TopoOrder(resources []model.Resource, adj map[string][]string) []string {
	byURN := map[string]model.Resource{}
	index := map[string]int{}
	for i, r := range resources {
		byURN[r.URN] = r
		index[r.URN] = i
	}
	indeg := map[string]int{}
	for _, r := range resources {
		if _, ok := indeg[r.URN]; !ok {
			indeg[r.URN] = 0
		}
	}
	for prereq, deps := range adj {
		for _, dep := range deps {
			indeg[dep]++
		}
		_ = prereq
	}

	ready := make([]string, 0)
	for _, r := range resources {
		if indeg[r.URN] == 0 {
			ready = append(ready, r.URN)
		}
	}
	sort.Strings(ready)

	order := make([]string, 0, len(resources))
	for len(ready) > 0 {
		cur := ready[0]
		ready = ready[1:]
		order = append(order, cur)
		for _, nxt := range adj[cur] {
			indeg[nxt]--
			if indeg[nxt] == 0 {
				ready = append(ready, nxt)
			}
		}
		sort.Strings(ready)
	}

	for _, r := range resources {
		if r.DeleteBeforeReplace && r.Replaces != "" {
			old := r.Replaces
			newU := r.URN
			order = moveBefore(order, newU, old)
		}
	}
	return order
}

func moveBefore(order []string, first, second string) []string {
	out := make([]string, 0, len(order))
	for _, u := range order {
		if u == second {
			continue
		}
		out = append(out, u)
		if u == first {
			out = append(out, second)
		}
	}
	return out
}
