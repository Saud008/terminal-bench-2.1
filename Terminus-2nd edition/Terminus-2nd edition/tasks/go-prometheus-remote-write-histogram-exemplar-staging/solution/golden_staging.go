package staging

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"promingest/internal/model"
)

const stagingDir = "/app/data/ingest"

type Record struct {
	Seed     string         `json:"seed"`
	Sequence int            `json:"sequence"`
	Series   []model.Series `json:"series"`
}

func Write(req *model.WriteRequest) error {
	if err := os.MkdirAll(stagingDir, 0o755); err != nil {
		return err
	}
	seq := 1
	if prev, err := Read(req.Seed); err == nil {
		seq = prev.Sequence + 1
	}
	rec := Record{Seed: req.Seed, Sequence: seq, Series: append([]model.Series(nil), req.Series...)}
	data, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	path := filepath.Join(stagingDir, req.Seed+".json")
	return os.WriteFile(path, data, 0o644)
}

func Read(seed string) (*Record, error) {
	path := filepath.Join(stagingDir, seed+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("staging missing: %w", err)
	}
	var rec Record
	if err := json.Unmarshal(data, &rec); err != nil {
		return nil, err
	}
	return &rec, nil
}

func PathFor(seed string) string {
	return filepath.Join(stagingDir, seed+".json")
}
