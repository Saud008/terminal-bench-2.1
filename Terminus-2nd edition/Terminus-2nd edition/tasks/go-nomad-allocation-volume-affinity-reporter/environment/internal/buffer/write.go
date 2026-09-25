package buffer

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/bundleloader"
	"github.com/terminus/nomad-allocation-volume-affinity-reporter/internal/model"
)

func WriteSnapshot(path, seed, scenario string, sc model.ScenarioFile) error {
	focus := bundleloader.ScopeAllocID(seed, sc.FocusAllocID)
	snap := model.BufferSnapshot{
		LoadSeq:      1,
		Seed:         seed,
		Scenario:     scenario,
		FocusAllocID: focus,
		JobID:        sc.JobID,
		TaskGroup:    sc.TaskGroup,
		StaleCutoff:  sc.StaleCutoffIndex,
		CSIVolumes:   sc.CSIVolumes,
		Allocations:  bundleloader.Materialize(sc, seed),
	}
	return writeJSON(path, snap)
}

func ReadSnapshot(path string) (model.BufferSnapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.BufferSnapshot{}, err
	}
	var snap model.BufferSnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.BufferSnapshot{}, err
	}
	return snap, nil
}

func ValidateSeedScenario(snap model.BufferSnapshot, seed, scenario string) error {
	if snap.Seed != seed || snap.Scenario != scenario {
		return fmt.Errorf("buffer seed/scenario mismatch")
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
