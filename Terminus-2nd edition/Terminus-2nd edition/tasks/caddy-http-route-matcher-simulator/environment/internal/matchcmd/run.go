package matchcmd

import (
	"os"

	"github.com/terminus/caddyctl/internal/matcher"
	"github.com/terminus/caddyctl/internal/staging"
	"github.com/terminus/caddyctl/internal/types"
)

// Run executes match against staged routes.
func Run(reqFile, stagePath, lastMatchPath string) error {
	st, err := staging.LoadStage(stagePath)
	if err != nil {
		return err
	}
	raw, err := os.ReadFile(reqFile)
	if err != nil {
		return err
	}
	req, err := matcher.ParseHTTPRequest(raw)
	if err != nil {
		return err
	}
	winner, ok := matcher.SelectWinner(st, req)
	lm := &types.LastMatch{Matched: ok}
	if ok {
		lm.HandlerID = winner.HandlerID
		lm.RouteIdx = winner.Index
	}
	return staging.SaveLastMatch(lastMatchPath, lm)
}
