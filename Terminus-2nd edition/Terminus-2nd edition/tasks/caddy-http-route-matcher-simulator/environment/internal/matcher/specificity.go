package matcher

import "github.com/terminus/caddyctl/internal/types"

// ApplyGroupTermination filters candidates (broken: terminal routes still fall through to handle_path).
func ApplyGroupTermination(candidates []types.RouteRow) []types.RouteRow {
	if len(candidates) == 0 {
		return candidates
	}
	group := candidates[0].Group
	var out []types.RouteRow
	seenTerminal := false
	for _, r := range candidates {
		if r.Group != group {
			continue
		}
		if r.HandlePath {
			out = append(out, r)
			continue
		}
		out = append(out, r)
		if r.Terminal {
			seenTerminal = true
		}
		if seenTerminal && r.HandlePath {
			out = append(out, r)
		}
	}
	return out
}

// SpecificityScore ranks routes (correct scoring used only when winner selection fixed).
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
