package matcher

import "github.com/terminus/caddyctl/internal/types"

func ApplyGroupTermination(candidates []types.RouteRow) []types.RouteRow {
	if len(candidates) == 0 {
		return candidates
	}
	var filtered []types.RouteRow
	for _, r := range candidates {
		if r.HandlePath {
			continue
		}
		filtered = append(filtered, r)
		if r.Terminal {
			break
		}
	}
	if len(filtered) == 0 {
		for _, r := range candidates {
			if r.HandlePath {
				filtered = append(filtered, r)
			}
		}
	}
	return filtered
}

func SpecificityScore(route types.RouteRow) int {
	score := 0
	for _, block := range route.Matchers {
		for _, p := range block.Path {
			if stringsHasSuffixStar(p) {
				score += 10
			} else {
				score += 30
			}
		}
		score += len(block.PathRegexp) * 20
		score += len(block.Header) * 15
		score += len(block.Method) * 5
	}
	return score
}
