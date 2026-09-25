package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/harbor/ldap-shadow-sync/internal/model"
)

const StagingPath = "/app/state/changelog-staging.jsonl"
const IngestStatsPath = "/app/state/last-ingest-stats.json"

func AppendChange(ch model.StagedChange) error {
	if err := os.MkdirAll(filepath.Dir(StagingPath), 0o755); err != nil {
		return err
	}
	f, err := os.OpenFile(StagingPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	b, err := json.Marshal(ch)
	if err != nil {
		return err
	}
	if _, err := f.Write(b); err != nil {
		return err
	}
	if _, err := f.Write([]byte("\n")); err != nil {
		return err
	}
	return nil
}

func ReadAll() ([]model.StagedChange, error) {
	b, err := os.ReadFile(StagingPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var out []model.StagedChange
	for _, line := range splitLines(b) {
		if len(line) == 0 {
			continue
		}
		var ch model.StagedChange
		if err := json.Unmarshal(line, &ch); err != nil {
			return nil, err
		}
		out = append(out, ch)
	}
	return out, nil
}

func WriteIngestStats(stats model.IngestStats) error {
	if err := os.MkdirAll(filepath.Dir(IngestStatsPath), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(stats, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(IngestStatsPath, b, 0o644)
}

func ReadIngestStats() (model.IngestStats, error) {
	b, err := os.ReadFile(IngestStatsPath)
	if err != nil {
		if os.IsNotExist(err) {
			return model.IngestStats{}, nil
		}
		return model.IngestStats{}, err
	}
	var stats model.IngestStats
	if err := json.Unmarshal(b, &stats); err != nil {
		return model.IngestStats{}, err
	}
	return stats, nil
}

func LineCount() (int, error) {
	rows, err := ReadAll()
	if err != nil {
		return 0, err
	}
	return len(rows), nil
}

func splitLines(b []byte) [][]byte {
	var lines [][]byte
	start := 0
	for i := 0; i < len(b); i++ {
		if b[i] == '\n' {
			lines = append(lines, b[start:i])
			start = i + 1
		}
	}
	if start < len(b) {
		lines = append(lines, b[start:])
	}
	return lines
}
