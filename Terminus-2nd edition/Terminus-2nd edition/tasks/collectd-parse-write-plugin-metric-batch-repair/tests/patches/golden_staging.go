package staging

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/collectdctl/internal/model"
)

const Path = "/app/state/collectd-ingest.snapshot.json"

type Envelope struct {
	Report        model.Report `json:"report"`
	IngestBinding string       `json:"ingest_binding"`
}

func Write(report model.Report) error {
	env := Envelope{
		Report:        report,
		IngestBinding: binding(report),
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
	if env.IngestBinding != binding(env.Report) {
		return fmt.Errorf("staging ingest_binding mismatch")
	}
	return nil
}

func binding(report model.Report) string {
	parts := []string{
		report.Seed,
		strings.Join(report.Batches, "\n"),
		fmt.Sprintf("%d", report.PipelineVersion),
		fmt.Sprintf("%d", report.Stats.Lines),
		fmt.Sprintf("%d", report.Stats.Accepted),
		fmt.Sprintf("%d", report.Stats.Rejected),
	}
	for _, flush := range report.Flushes {
		parts = append(parts, fmt.Sprintf("%d", flush.FlushIndex))
		parts = append(parts, fmt.Sprintf("%d", flush.StartEpoch))
		parts = append(parts, fmt.Sprintf("%d", flush.EndEpoch))
		for _, metric := range flush.Metrics {
			b, _ := json.Marshal(metric)
			parts = append(parts, string(b))
		}
	}
	sum := sha256.Sum256([]byte(strings.Join(parts, "\n")))
	return hex.EncodeToString(sum[:])
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
