package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/temporal-signal-replay/internal/model"
)

const SnapshotPath = "/app/state/signal-snapshot.json"

func WriteSnapshot(snap model.Snapshot) error {
	snap.StagingWritten = false
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(SnapshotPath, append(raw, '\n'), 0o644)
}

func LoadSnapshot() (model.Snapshot, error) {
	raw, err := os.ReadFile(SnapshotPath)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}
