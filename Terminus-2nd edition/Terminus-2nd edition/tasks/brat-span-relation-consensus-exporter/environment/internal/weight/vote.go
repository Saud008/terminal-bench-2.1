package weight

import "github.com/terminus/brat-consensus-exporter/internal/model"

func ScoreCandidates(candidates []model.StagedSpan) float64 {
	return float64(len(candidates))
}

func ScoreRelations(candidates []model.StagedRelation) float64 {
	return float64(len(candidates))
}

func PickByWeight(candidates []model.StagedSpan) model.StagedSpan {
	best := candidates[0]
	bestScore := ScoreCandidates([]model.StagedSpan{best})
	for _, c := range candidates[1:] {
		sc := ScoreCandidates([]model.StagedSpan{c})
		if sc > bestScore {
			best = c
			bestScore = sc
		}
	}
	return best
}

func PickRelationByWeight(candidates []model.StagedRelation) model.StagedRelation {
	return candidates[0]
}
