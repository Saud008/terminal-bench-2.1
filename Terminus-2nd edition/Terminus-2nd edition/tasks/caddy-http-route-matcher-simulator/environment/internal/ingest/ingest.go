package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/caddyctl/internal/staging"
	"github.com/terminus/caddyctl/internal/types"
)

// IngestDirectory reads JSON route files and writes staging + commit metadata.
func IngestDirectory(dir, stagePath, commitPath string) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}
	var names []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if strings.HasSuffix(e.Name(), ".json") {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)

	st := &types.StageFile{Routes: []types.RouteRow{}}
	idx := 0
	for _, name := range names {
		data, err := os.ReadFile(filepath.Join(dir, name))
		if err != nil {
			return err
		}
		var cfg types.RouteConfig
		if err := json.Unmarshal(data, &cfg); err != nil {
			return fmt.Errorf("%s: %w", name, err)
		}
		for _, r := range cfg.Routes {
			st.Routes = append(st.Routes, types.RouteRow{
				Index:      idx,
				HandlerID:  r.ID,
				Group:      r.Group,
				Terminal:   r.Terminal,
				HandlePath: r.HandlePath,
				Matchers:   r.Match,
				Source:     name,
			})
			idx++
		}
	}

	prev, _ := staging.LoadCommit(commitPath)
	seq := 1
	if prev != nil {
		seq = prev.ReplaySeq + 1
	}
	st.IngestSeq = seq

	if err := staging.SaveStage(stagePath, st); err != nil {
		return err
	}
	return staging.SaveCommit(commitPath, &types.CommitFile{
		ReplaySeq: seq,
		StageHash: staging.StageHash(st),
	})
}
