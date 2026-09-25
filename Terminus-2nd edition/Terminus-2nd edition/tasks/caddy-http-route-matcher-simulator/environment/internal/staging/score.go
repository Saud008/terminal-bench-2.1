package staging

import (
	"strings"

	"github.com/terminus/caddyroute/internal/types"
)

// ScoreRoute returns a specificity weight for matchers on a route.
func ScoreRoute(route types.Route) int {
	score := 0
	for _, m := range route.Match {
		for _, p := range m.Path {
			if strings.HasSuffix(p, "*") {
				score += 10
			} else {
				score += 30
			}
		}
		score += len(m.PathRegexp) * 8
		score += len(m.Method) * 5
		for range m.Header {
			score += 6
		}
	}
	return score
}
