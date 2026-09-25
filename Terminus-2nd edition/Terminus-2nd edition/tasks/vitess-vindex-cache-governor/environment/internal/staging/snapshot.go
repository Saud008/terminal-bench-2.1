package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"vtgatesim/internal/model"
)

func WriteSnapshot(path string, snap model.Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func ReadSnapshot(path string) (model.Snapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(data, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}
