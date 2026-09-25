package match

import (
	"errors"
	"os"

	"github.com/terminus/caddyroute/internal/staging"
	"github.com/terminus/caddyroute/internal/types"
)

var errNoMatch = errors.New("no route matched")

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
	row, ok := PickWinner(st, req)
	if !ok {
		return types.MatchResult{}, errNoMatch
	}
	return types.MatchResult{
		HandlerID:   row.ID,
		RouteIndex:  row.SourceIndex,
		Specificity: row.Specificity,
	}, nil
}
