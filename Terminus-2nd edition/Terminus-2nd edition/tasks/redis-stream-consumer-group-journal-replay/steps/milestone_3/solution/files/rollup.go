package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/redisstream/internal/staging"
	"github.com/terminus/redisstream/internal/types"
)

const DefaultRollupPath = "/app/output/stream-rollup.json"

func BuildRollup(stagePath, outPath string, exportPass int) error {
	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}
	rollup := types.RollupFile{
		StreamLengths: map[string]int{},
		Groups:        []types.RollupGroup{},
		ExportPass:    exportPass,
	}
	for name, stream := range st.Streams {
		rollup.StreamLengths[name] = len(stream.Entries)
		for gname, grp := range stream.Groups {
			rollup.Groups = append(rollup.Groups, types.RollupGroup{
				Stream:       name,
				Group:        gname,
				PELDistinct:  len(grp.Pending),
				ReclaimTotal: grp.ReclaimTotal,
			})
		}
	}
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(rollup, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}
