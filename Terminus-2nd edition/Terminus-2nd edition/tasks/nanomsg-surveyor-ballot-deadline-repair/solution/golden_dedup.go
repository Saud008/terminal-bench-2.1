package topology

import "github.com/terminus/ballotmesh/internal/model"

func VoteWeight(topo model.Topology, respondent string) int {
	if topo.Kind != "star" {
		return 1
	}
	seen := map[string]bool{}
	for _, e := range topo.Edges {
		a, b := e[0], e[1]
		if a > b {
			a, b = b, a
		}
		key := a + "|" + b
		if seen[key] {
			continue
		}
		seen[key] = true
		_ = respondent
	}
	return 1
}
