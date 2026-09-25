package weight

import "github.com/terminus/brat-consensus-exporter/internal/model"

func ScoreCandidates(candidates []model.StagedSpan) float64 {
	var total float64
	for _, c := range candidates {
		total += c.Weight
	}
	return total
}

func ScoreRelations(candidates []model.StagedRelation) float64 {
	var total float64
	for _, c := range candidates {
		total += c.Weight
	}
	return total
}

func PickByWeight(candidates []model.StagedSpan) model.StagedSpan {
	best := candidates[0]
	for _, c := range candidates[1:] {
		if c.Weight > best.Weight {
			best = c
		}
	}
	return best
}

func PickRelationByWeight(candidates []model.StagedRelation) model.StagedRelation {
	best := candidates[0]
	for _, c := range candidates[1:] {
		if c.Weight > best.Weight {
			best = c
		}
	}
	return best
}
