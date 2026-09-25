package export

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/natsjetstream/internal/staging"
	"github.com/terminus/natsjetstream/internal/types"
)

const DefaultRollupPath = "/app/output/pending-rollup.json"

// BuildRollup reads stage state and writes pending rollup export.
func BuildRollup(stagePath, outPath string, exportPass int) error {
	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}
	rollup := types.RollupFile{ExportPass: exportPass}
	for sname, stream := range st.Streams {
		// Baseline bug: use stream max seq for every consumer high-water row.
		streamHigh := stream.MaxSeq
		for cname, cons := range stream.Consumers {
			due := 0
			for _, p := range cons.Pending {
				if p.RedeliveryDueTick > 0 && p.RedeliveryDueTick <= cons.TickLedger {
					due++
				}
			}
			rollup.Consumers = append(rollup.Consumers, types.RollupConsumer{
				Stream:        sname,
				Consumer:      cname,
				PendingCount:  len(cons.Pending),
				HighWaterSeq:  streamHigh,
				RedeliveryDue: due,
			})
		}
	}
	sort.Slice(rollup.Consumers, func(i, j int) bool {
		if rollup.Consumers[i].Stream != rollup.Consumers[j].Stream {
			return rollup.Consumers[i].Stream < rollup.Consumers[j].Stream
		}
		return rollup.Consumers[i].Consumer < rollup.Consumers[j].Consumer
	})
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
