package export

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/caddyctl/internal/staging"
)

const DefaultOutputPath = "/app/output/route-handler.json"

type outputDoc struct {
	HandlerID string `json:"handler_id"`
	ReplaySeq int    `json:"replay_seq"`
	RouteIdx  int    `json:"route_index"`
}

// RouteExport writes handler selection from last match (broken: uses route index as handler_id).
func RouteExport(stagePath, lastMatchPath, commitPath, outPath string) error {
	_, err := staging.LoadStage(stagePath)
	if err != nil {
		return err
	}
	lm, err := staging.LoadLastMatch(lastMatchPath)
	if err != nil {
		return err
	}
	commit, err := staging.LoadCommit(commitPath)
	if err != nil {
		return err
	}
	if !lm.Matched {
		return errNoMatch
	}
	handler := fmt.Sprintf("route-index-%d", lm.RouteIdx)
	doc := outputDoc{
		HandlerID: handler,
		ReplaySeq: commit.ReplaySeq,
		RouteIdx:  lm.RouteIdx,
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}

var errNoMatch = &exportError{"no match to export"}

type exportError struct{ msg string }

func (e *exportError) Error() string { return e.msg }
