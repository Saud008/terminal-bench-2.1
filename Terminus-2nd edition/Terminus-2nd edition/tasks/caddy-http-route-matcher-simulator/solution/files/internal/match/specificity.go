package match

import (
	"encoding/json"
	"sort"
	"strings"

	"github.com/terminus/caddyroute/internal/types"
)

// ScoreRoute returns a specificity weight for a route (higher is more specific).
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

// PickWinner chooses the most specific staged route that matches the request.
func PickWinner(st *types.StageFile, req types.HTTPRequest) (types.StagedRoute, bool) {
	type candidate struct {
		row types.StagedRoute
	}
	var hits []candidate
	for _, row := range st.Routes {
		var matchers []types.Matcher
		if err := json.Unmarshal([]byte(row.MatcherJSON), &matchers); err != nil {
			continue
		}
		if RouteMatches(matchers, req, row.Terminal) {
			hits = append(hits, candidate{row: row})
		}
	}
	if len(hits) == 0 {
		return types.StagedRoute{}, false
	}
	sort.Slice(hits, func(i, j int) bool {
		if hits[i].row.Specificity != hits[j].row.Specificity {
			return hits[i].row.Specificity > hits[j].row.Specificity
		}
		return hits[i].row.ID < hits[j].row.ID
	})
	return hits[0].row, true
}
