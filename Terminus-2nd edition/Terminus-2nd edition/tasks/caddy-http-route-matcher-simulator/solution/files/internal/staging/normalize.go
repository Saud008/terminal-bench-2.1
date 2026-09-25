package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/caddyroute/internal/types"
)

const DefaultStagePath = "/app/state/route-stage.json"

// Normalize builds a staging ledger from a route file, flattening nested handle_path routes.
func Normalize(rf *types.RouteFile, sourcePath string) (*types.StageFile, error) {
	st := &types.StageFile{
		SourcePath: sourcePath,
		Routes:     []types.StagedRoute{},
		HandlerMap: map[string]int{},
	}
	var walk func(routes []types.Route, parent []types.Matcher)
	walk = func(routes []types.Route, parent []types.Matcher) {
		for _, route := range routes {
			combined := append(append([]types.Matcher{}, parent...), route.Match...)
			if route.ID != "" && len(route.Handle) > 0 {
				mj, err := json.Marshal(combined)
				if err != nil {
					return
				}
				hj, err := json.Marshal(route.Handle)
				if err != nil {
					return
				}
				spec := ScoreRoute(types.Route{Match: combined})
				pos := len(st.Routes)
				st.Routes = append(st.Routes, types.StagedRoute{
					ID:          route.ID,
					Specificity: spec,
					SourceIndex: pos,
					Terminal:    route.Terminal,
					MatcherJSON: string(mj),
					HandleJSON:  string(hj),
				})
				st.HandlerMap[route.ID] = pos
			}
			if len(route.Routes) > 0 {
				walk(route.Routes, combined)
			}
		}
	}
	walk(rf.Routes, nil)
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
