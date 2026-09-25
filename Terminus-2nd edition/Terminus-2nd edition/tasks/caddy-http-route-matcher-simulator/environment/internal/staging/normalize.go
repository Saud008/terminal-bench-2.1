package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/caddyroute/internal/types"
)

const DefaultStagePath = "/app/state/route-stage.json"

// Normalize builds a staging ledger from a route file.
func Normalize(rf *types.RouteFile, sourcePath string) (*types.StageFile, error) {
	st := &types.StageFile{
		SourcePath: sourcePath,
		Routes:     []types.StagedRoute{},
		HandlerMap: map[string]int{},
	}
	for i, route := range rf.Routes {
		if route.ID == "" {
			continue
		}
		mj, err := json.Marshal(route.Match)
		if err != nil {
			return nil, err
		}
		hj, err := json.Marshal(route.Handle)
		if err != nil {
			return nil, err
		}
		spec := ScoreRoute(route)
		st.Routes = append(st.Routes, types.StagedRoute{
			ID:          route.ID,
			Specificity: spec,
			SourceIndex: i,
			Terminal:    route.Terminal,
			MatcherJSON: string(mj),
			HandleJSON:  string(hj),
		})
		st.HandlerMap[route.ID] = i
	}
	return st, nil
}

// Save writes the staging file with stable formatting.
func Save(path string, st *types.StageFile) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

// Load reads a staging ledger from disk.
func Load(path string) (*types.StageFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var st types.StageFile
	if err := json.Unmarshal(data, &st); err != nil {
		return nil, err
	}
	return &st, nil
}
