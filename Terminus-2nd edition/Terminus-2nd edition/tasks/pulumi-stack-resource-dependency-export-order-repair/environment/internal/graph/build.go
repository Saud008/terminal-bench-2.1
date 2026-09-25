package graph

import (
	"github.com/terminus/pulumi-dep-export/internal/model"
)

// FlattenComponents rewires component children to the component's parent.
func FlattenComponents(resources []model.Resource) []model.Resource {
	byURN := map[string]model.Resource{}
	for _, r := range resources {
		byURN[r.URN] = r
	}
	out := make([]model.Resource, len(resources))
	copy(out, resources)
	for i, r := range out {
		if r.Parent == "" {
			continue
		}
		parent, ok := byURN[r.Parent]
		if !ok || !parent.Component {
			continue
		}
		out[i].Parent = parent.Parent
	}
	return out
}

// BuildAdjacency returns prerequisite -> dependents (prerequisite must export first).
func BuildAdjacency(resources []model.Resource) map[string][]string {
	adj := map[string][]string{}
	known := map[string]bool{}
	for _, r := range resources {
		known[r.URN] = true
	}
	for _, r := range resources {
		for _, dep := range r.Dependencies {
			if !known[dep] {
				continue
			}
			adj[dep] = append(adj[dep], r.URN)
			adj[r.URN] = append(adj[r.URN], dep)
		}
	}
	return adj
}
