package export

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/collectdctl/internal/model"
	"github.com/terminus/collectdctl/internal/staging"
)

func Write(path string, env staging.Envelope) error {
	report := env.Report
	flushes := make([]model.FlushExport, len(report.Flushes))
	for i, flush := range report.Flushes {
		metrics := append([]model.MetricExport{}, flush.Metrics...)
		sort.Slice(metrics, func(a, b int) bool {
			return metrics[a].Value > metrics[b].Value
		})
		flushes[i] = model.FlushExport{
			FlushIndex: flush.FlushIndex,
			StartEpoch: flush.StartEpoch,
			EndEpoch:   flush.EndEpoch,
			Metrics:    metrics,
		}
	}
	out := model.Report{
		PipelineVersion: report.PipelineVersion,
		Seed:            report.Seed,
		Batches:         report.Batches,
		Flushes:         flushes,
		Stats:           report.Stats,
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}
