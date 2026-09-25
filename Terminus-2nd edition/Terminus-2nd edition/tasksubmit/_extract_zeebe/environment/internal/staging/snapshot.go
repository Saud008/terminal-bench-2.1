package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/zeebe-bpmn-replay/internal/model"
)

const snapshotPath = "/app/state/incident-snapshot.json"

func WriteSnapshot(snap model.Snapshot) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(snapshotPath, append(raw, '\n'), 0o644)
}

func LoadSnapshot() (model.Snapshot, error) {
	raw, err := os.ReadFile(snapshotPath)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}
