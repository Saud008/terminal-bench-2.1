package match

import (
	"encoding/json"

	"github.com/terminus/caddyroute/internal/types"
)

// PickWinner chooses the winning staged route for a request.
func PickWinner(st *types.StageFile, req types.HTTPRequest) (types.StagedRoute, bool) {
	for _, row := range st.Routes {
		var matchers []types.Matcher
		if err := json.Unmarshal([]byte(row.MatcherJSON), &matchers); err != nil {
			continue
		}
		if RouteMatches(matchers, req, row.Terminal) {
			return row, true
		}
	}
	return types.StagedRoute{}, false
}
