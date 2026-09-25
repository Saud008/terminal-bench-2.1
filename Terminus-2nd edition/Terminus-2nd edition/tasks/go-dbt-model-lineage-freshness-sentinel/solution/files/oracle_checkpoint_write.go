package packstate

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"
	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/packload"
)

func WriteSnapshot(path, seed, bundle string, raw model.ManifestBundle) error {
	prev := int64(0)
	if b, err := os.ReadFile(path); err == nil {
		var old model.StagingSnapshot
		if json.Unmarshal(b, &old) == nil {
			prev = old.IngestSeq
		}
	}
	mat := packload.Materialize(raw, seed)
	snap := model.StagingSnapshot{
		IngestSeq:   prev + 1,
		Seed:        seed,
		Pack:        bundle,
		GeneratedAt: raw.GeneratedAt,
		EvaluatedAt: raw.EvaluatedAt,
		Models:      mat.Models,
		Sources:     mat.Sources,
		Exposures:   mat.Exposures,
	}
	return writeJSON(path, snap)
}

func ReadSnapshot(path string) (model.StagingSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.StagingSnapshot{}, err
	}
	var snap model.StagingSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.StagingSnapshot{}, err
	}
	return snap, nil
}

func ValidateSeedBundle(snap model.StagingSnapshot, seed, bundle string) error {
	if snap.Seed != seed || snap.Pack != bundle {
		return fmt.Errorf("staging seed/bundle mismatch")
	}
	return nil
}

func writeJSON(path string, v any) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}
