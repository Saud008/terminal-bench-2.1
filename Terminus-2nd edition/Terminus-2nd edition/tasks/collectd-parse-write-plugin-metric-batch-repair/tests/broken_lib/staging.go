package staging

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/collectdctl/internal/model"
)

const Path = "/app/state/collectd-ingest.snapshot.json"

type Envelope struct {
	Report        model.Report `json:"report"`
	IngestBinding string       `json:"ingest_binding"`
}

func Write(report model.Report) error {
	flushes := report.Flushes
	reversed := make([]model.FlushExport, len(flushes))
	for i := range flushes {
		f := flushes[len(flushes)-1-i]
		metrics := append([]model.MetricExport{}, f.Metrics...)
		for j, k := 0, len(metrics)-1; j < k; j, k = j+1, k-1 {
			metrics[j], metrics[k] = metrics[k], metrics[j]
		}
		reversed[i] = model.FlushExport{
			FlushIndex: f.FlushIndex,
			StartEpoch: f.StartEpoch,
			EndEpoch:   f.EndEpoch,
			Metrics:    metrics,
		}
	}
	env := Envelope{
		Report: model.Report{
			PipelineVersion: report.PipelineVersion,
			Seed:            report.Seed,
			Batches:         report.Batches,
			Flushes:         reversed,
			Stats:           report.Stats,
		},
		IngestBinding: fmt.Sprintf("flushes:%d", len(report.Flushes)),
	}
	return writeEnvelope(env)
}

func Read() (Envelope, error) {
	data, err := os.ReadFile(Path)
	if err != nil {
		return Envelope{}, err
	}
	var env Envelope
	if err := json.Unmarshal(data, &env); err != nil {
		return Envelope{}, err
	}
	return env, nil
}

func Verify(env Envelope) error {
	return nil
}

func writeEnvelope(env Envelope) error {
	if err := os.MkdirAll(filepath.Dir(Path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(env, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(Path, append(data, '\n'), 0o644)
}
