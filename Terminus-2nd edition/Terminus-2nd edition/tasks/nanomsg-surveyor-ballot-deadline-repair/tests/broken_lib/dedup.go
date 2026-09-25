package topology

import "github.com/terminus/ballotmesh/internal/model"

// VoteWeight returns how many times a respondent vote counts toward total_weighted.
func VoteWeight(topo model.Topology, respondent string) int {
	if topo.Kind != "star" {
		return 1
	}
	count := 0
	for _, e := range topo.Edges {
		if e[0] == respondent || e[1] == respondent {
			count++
		}
	}
	if count == 0 {
		return 1
	}
	return count
}
