package match

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/caddyroute/internal/staging"
	"github.com/terminus/caddyroute/internal/types"
)

// SimulateMatch loads staging and returns the selected handler for a request file.
func SimulateMatch(stagePath, requestPath string) (types.MatchResult, error) {
	st, err := staging.Load(stagePath)
	if err != nil {
		return types.MatchResult{}, err
	}
	raw, err := os.ReadFile(requestPath)
	if err != nil {
		return types.MatchResult{}, err
	}
	req, err := ParseHTTPRequest(raw)
	if err != nil {
		return types.MatchResult{}, err
	}

	var last types.StagedRoute
	found := false
	for _, row := range st.Routes {
		var matchers []types.Matcher
		if err := json.Unmarshal([]byte(row.MatcherJSON), &matchers); err != nil {
			continue
		}
		if RouteMatches(matchers, req, row.Terminal) {
			last = row
			found = true
		}
	}
	if !found {
		return types.MatchResult{}, fmt.Errorf("no route matched")
	}
	return types.MatchResult{
		HandlerID:   last.ID,
		RouteIndex:  last.SourceIndex,
		Specificity: last.Specificity,
	}, nil
}
