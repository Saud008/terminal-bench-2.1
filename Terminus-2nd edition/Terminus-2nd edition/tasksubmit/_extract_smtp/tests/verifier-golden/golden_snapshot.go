package staging

import (

	"encoding/json"

	"fmt"

	"os"

	"path/filepath"

	"mailindex/internal/model"

)

const snapshotPath = "/app/state/thread-index.snapshot.json"

func WriteIndexSnapshot(threadDB string, report model.Report) error {

	snap := model.SnapshotFromReport(threadDB, report)

	snap.IndexDigest = FinalizeIndexDigest(report.MessagesIndexedList, report.ThreadsResolved)

	if err := os.MkdirAll(filepath.Dir(snapshotPath), 0o755); err != nil {

		return err

	}

	raw, err := json.MarshalIndent(snap, "", "  ")

	if err != nil {

		return err

	}

	return os.WriteFile(snapshotPath, raw, 0o644)

}

func ReadIndexSnapshot() (model.IndexSnapshot, error) {

	raw, err := os.ReadFile(snapshotPath)

	if err != nil {

		if os.IsNotExist(err) {

			return model.IndexSnapshot{}, fmt.Errorf("index snapshot missing at %s", snapshotPath)

		}

		return model.IndexSnapshot{}, err

	}

	var snap model.IndexSnapshot

	if err := json.Unmarshal(raw, &snap); err != nil {

		return model.IndexSnapshot{}, err

	}

	return snap, nil

}

func SnapshotPath() string {

	return snapshotPath

}
