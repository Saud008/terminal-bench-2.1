package pipeline

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/collectdctl/internal/config"
	"github.com/terminus/collectdctl/internal/export"
	"github.com/terminus/collectdctl/internal/flush"
	"github.com/terminus/collectdctl/internal/model"
	"github.com/terminus/collectdctl/internal/normalize"
	"github.com/terminus/collectdctl/internal/parse"
	"github.com/terminus/collectdctl/internal/staging"
)

func Run(textPath, cfgPath, outPath string) (int, error) {
	if err := Stage(textPath, cfgPath); err != nil {
		return 2, err
	}
	return Export(outPath)
}

func Stage(textPath, cfgPath string) error {
	report, err := BuildReport(textPath, cfgPath)
	if err != nil {
		return err
	}
	return staging.Write(report)
}

func Export(outPath string) (int, error) {
	env, err := staging.Read()
	if err != nil {
		return 2, fmt.Errorf("staging snapshot missing")
	}
	// Broken: rebuild report from staged batch files instead of publishing staged snapshot.
	cfg, err := config.Load("/app/config/ingest.json")
	if err != nil {
		return 2, err
	}
	var contents []string
	for _, name := range env.Report.Batches {
		raw, readErr := os.ReadFile(filepath.Join("/app/fixtures/batches", name))
		if readErr != nil {
			return 2, readErr
		}
		contents = append(contents, string(raw))
	}
	report, err := ingestBatches(cfg, env.Report.Batches, contents)
	if err != nil {
		return 2, err
	}
	env = staging.Envelope{Report: report, IngestBinding: env.IngestBinding}
	if err := export.Write(outPath, env); err != nil {
		return 2, err
	}
	return 0, nil
}

func BuildReport(textPath, cfgPath string) (model.Report, error) {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return model.Report{}, err
	}

	var batches []string
	var contents []string
	if textPath != "" {
		raw, err := os.ReadFile(textPath)
		if err != nil {
			return model.Report{}, err
		}
		batches = []string{filepath.Base(textPath)}
		contents = []string{string(raw)}
	} else {
		batches = config.SelectBatches(cfg.Seed, cfg.Batches)
		for _, name := range batches {
			raw, err := os.ReadFile(filepath.Join("/app/fixtures/batches", name))
			if err != nil {
				return model.Report{}, err
			}
			contents = append(contents, string(raw))
		}
	}
	return ingestBatches(cfg, batches, contents)
}

func ingestBatches(cfg model.Config, batches []string, contents []string) (model.Report, error) {
	stats := model.Stats{}
	type seriesKey struct {
		id string
		ds string
	}
	seriesBuckets := map[seriesKey][]model.NormalizedPoint{}

	for _, content := range contents {
		anchor := int64(-1)
		readings, err := parse.ParseStream(content)
		if err != nil {
			return model.Report{}, err
		}
		stats.Lines += len(readings)
		for _, raw := range readings {
			points := normalize.ExpandReadings(raw, cfg.TypesDB)
			for _, pt := range points {
				if pt.Epoch < cfg.EpochOrigin {
					stats.Rejected++
					continue
				}
				if anchor < 0 {
					anchor = pt.Epoch
				}
				if !flush.WithinSkew(pt.Epoch, anchor, cfg.TimeSkewSec) {
					stats.Rejected++
					continue
				}
				stats.Accepted++
				key := seriesKey{id: pt.CanonicalID, ds: pt.DS}
				seriesBuckets[key] = append(seriesBuckets[key], pt)
			}
		}
	}

	flushes := map[int64][]model.MetricExport{}
	for key, pts := range seriesBuckets {
		kind := cfg.TypesDB[parse.TypeName(key.id)][key.ds]
		normalized := normalize.PairRates(pts, kind)
		for _, pt := range normalized {
			idx := flush.FlushIndex(pt.Epoch, cfg.EpochOrigin, cfg.FlushIntervalSec)
			if idx < 0 {
				continue
			}
			flushes[idx] = append(flushes[idx], model.MetricExport{
				CanonicalID: pt.CanonicalID,
				DS:          pt.DS,
				ValueKind:   pt.ValueKind,
				Epoch:       pt.Epoch,
				Value:       pt.Value,
			})
		}
	}

	indices := make([]int64, 0, len(flushes))
	for idx := range flushes {
		indices = append(indices, idx)
	}
	sort.Slice(indices, func(i, j int) bool { return indices[i] < indices[j] })

	outFlushes := make([]model.FlushExport, 0, len(indices))
	for _, idx := range indices {
		metrics := flushes[idx]
		sort.Slice(metrics, func(i, j int) bool {
			if metrics[i].CanonicalID != metrics[j].CanonicalID {
				return metrics[i].CanonicalID < metrics[j].CanonicalID
			}
			if metrics[i].DS != metrics[j].DS {
				return metrics[i].DS < metrics[j].DS
			}
			return metrics[i].Epoch < metrics[j].Epoch
		})
		start, end := flush.FlushBounds(idx, cfg.EpochOrigin, cfg.FlushIntervalSec)
		outFlushes = append(outFlushes, model.FlushExport{
			FlushIndex: int(idx),
			StartEpoch: start,
			EndEpoch:   end,
			Metrics:    metrics,
		})
	}

	return model.Report{
		PipelineVersion: 1,
		Seed:            cfg.Seed,
		Batches:         batches,
		Flushes:         outFlushes,
		Stats:           stats,
	}, nil
}
