// Package staging materializes feature-run snapshots for numerical closure simulation.
package staging

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/mlflow-provenance-curator/internal/ingest"
	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

// WriteSnapshot baseline never increments ingest_seq.
func WriteSnapshot(path, seed, scenario string, sc model.ScenarioFile) error {
	focus := ingest.ScopeRunID(seed, sc.FocusRunID)
	snap := model.StagingSnapshot{
		IngestSeq:        0,
		Seed:             seed,
		Scenario:         scenario,
		FocusRunID:       focus,
		ExperimentID:     sc.ExperimentID,
		DatasetManifests: sc.DatasetManifests,
		Runs:             ingest.Materialize(sc, seed),
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

func ValidateSeedScenario(snap model.StagingSnapshot, seed, scenario string) error {
	if snap.Seed != seed || snap.Scenario != scenario {
		return fmt.Errorf("staging seed/scenario mismatch")
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
