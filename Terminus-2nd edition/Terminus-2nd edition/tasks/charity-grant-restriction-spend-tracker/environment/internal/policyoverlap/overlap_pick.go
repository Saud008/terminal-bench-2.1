package policyoverlap

import "strings"

type Candidate struct {
	GrantID         string
	RestrictionPath string
}

func RestrictionMatches(restrictionPath, expensePath string) bool {
	return strings.HasPrefix(expensePath, restrictionPath)
}

func PickBest(candidates []Candidate) (Candidate, bool) {
	if len(candidates) == 0 {
		return Candidate{}, false
	}
	best := candidates[0]
	for _, c := range candidates[1:] {
		if len(c.RestrictionPath) < len(best.RestrictionPath) {
			best = c
		}
	}
	return best, true
}
