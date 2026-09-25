package placement

import (
	"sort"
	"strings"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/spread"
)

func nodeClassMatch(c model.Constraint, nodeClass string) bool {
	if c.Attribute != "${node.class}" {
		return true
	}
	switch c.Operator {
	case "=":
		return nodeClass == c.Value
	case "!=":
		return nodeClass != c.Value
	default:
		return false
	}
}

func affinityScore(a model.Affinity, nodePool string) int {
	if a.Attribute != "${node.pool}" {
		return 0
	}
	switch a.Operator {
	case "=":
		if nodePool == a.Value {
			return a.Weight
		}
	case "!=":
		if nodePool != a.Value {
			return a.Weight
		}
	}
	return 0
}

func RankPlacements(allocs []model.ScopedAllocation, nodePool string) []model.PlacementRow {
	type row struct {
		alloc model.ScopedAllocation
		score int
		hard  bool
	}
	passing := make([]row, 0, len(allocs))
	for _, a := range allocs {
		hardOK := true
		for _, c := range a.Constraints {
			if c.Hard && !nodeClassMatch(c, a.NodeClass) {
				hardOK = false
				break
			}
		}
		if !hardOK {
			continue
		}
		raw := 0
		for _, af := range a.Affinities {
			raw += affinityScore(af, nodePool)
		}
		score := spread.AdjustScore(raw, a, allocs)
		passing = append(passing, row{alloc: a, score: score, hard: hardOK})
	}
	sort.Slice(passing, func(i, j int) bool {
		if passing[i].score != passing[j].score {
			return passing[i].score > passing[j].score
		}
		return passing[i].alloc.AllocID < passing[j].alloc.AllocID
	})
	out := make([]model.PlacementRow, 0, len(passing))
	for i, p := range passing {
		out = append(out, model.PlacementRow{
			AllocID:       p.alloc.AllocID,
			NodeClass:     p.alloc.NodeClass,
			ConstraintOK:  p.hard,
			AffinityScore: p.score,
			PlacementRank: i + 1,
		})
	}
	return out
}

func ConstraintPass(allocs []model.ScopedAllocation) bool {
	for _, a := range allocs {
		for _, c := range a.Constraints {
			if c.Hard && strings.Contains(c.Attribute, "node.class") && !nodeClassMatch(c, a.NodeClass) {
				return false
			}
		}
	}
	return true
}
