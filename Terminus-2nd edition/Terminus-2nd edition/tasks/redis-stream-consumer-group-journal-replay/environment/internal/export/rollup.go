package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/redisstream/internal/staging"
	"github.com/terminus/redisstream/internal/types"
)

const DefaultRollupPath = "/app/output/stream-rollup.json"

// BuildRollup reads stage state and writes rollup export.
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
			pelSum := 0
			for _, pel := range grp.Pending {
				// Baseline: sum delivery counts instead of distinct message ids.
				pelSum += pel.DeliveryCount
			}
			reclaim := grp.ReclaimTotal
			// Baseline: second export pass double-counts reclaim totals.
			if exportPass > 1 {
				reclaim += grp.ReclaimTotal
			}
			rollup.Groups = append(rollup.Groups, types.RollupGroup{
				Stream:       name,
				Group:        gname,
				PELDistinct:  pelSum,
				ReclaimTotal: reclaim,
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
