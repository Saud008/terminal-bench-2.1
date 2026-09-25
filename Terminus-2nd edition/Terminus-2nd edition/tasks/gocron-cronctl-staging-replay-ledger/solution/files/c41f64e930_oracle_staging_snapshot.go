package staging

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/terminus/gocron-overlap-repair/internal/croncalc"
	"github.com/terminus/gocron-overlap-repair/internal/model"
)

func WriteSnapshot(path string, seed, scenario string, sc model.Scenario, defaultLoc string) error {
	fires, err := croncalc.ComputeFires(sc, defaultLoc)
	if err != nil {
		return err
	}
	sort.Slice(fires, func(i, j int) bool {
		if fires[i].AtMs == fires[j].AtMs {
			return fires[i].JobID < fires[j].JobID
		}
		return fires[i].AtMs < fires[j].AtMs
	})
	snap := model.Snapshot{
		Seed:             seed,
		Scenario:         scenario,
		Location:         defaultLoc,
		Engine:           "croncalc",
		FiresDigest:      ComputeFiresDigest(fires),
		ReplayGeneration: 0,
		PlannedFires:     fires,
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(path, raw, 0o644); err != nil {
		return err
	}
	return ResetGeneration(GenerationPath(), seed, scenario)
}

func ReadSnapshot(path string) (model.Snapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}

func UpdateReplayGeneration(snapshotPath string, gen int) error {
	snap, err := ReadSnapshot(snapshotPath)
	if err != nil {
		return err
	}
	snap.ReplayGeneration = gen
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(snapshotPath, raw, 0o644)
}
