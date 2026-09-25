package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/asynq-archive-repair/internal/model"
)

func WriteSnapshot(path string, snap model.Snapshot) error {
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
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
