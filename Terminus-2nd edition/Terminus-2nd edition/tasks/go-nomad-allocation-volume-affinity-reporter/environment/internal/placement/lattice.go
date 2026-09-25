package placement

import (
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
	rows := make([]model.PlacementRow, 0, len(allocs))
	for i, a := range allocs {
		score := 0
		for _, af := range a.Affinities {
			score += affinityScore(af, nodePool)
		}
		score = spread.AdjustScore(score, a, allocs)
		hardOK := true
		for _, c := range a.Constraints {
			if c.Hard && !nodeClassMatch(c, a.NodeClass) {
				hardOK = false
			}
		}
		rows = append(rows, model.PlacementRow{
			AllocID:       a.AllocID,
			NodeClass:     a.NodeClass,
			ConstraintOK:  hardOK,
			AffinityScore: score,
			PlacementRank: i + 1,
		})
	}
	return rows
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
