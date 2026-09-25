package staging

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/harbor/tug-berth/internal/model"
)

const SnapshotPath = "/app/state/ingest-snapshot.json"

func WriteSnapshot(rows []model.SnapshotRow) error {
	if err := os.MkdirAll(filepath.Dir(SnapshotPath), 0o755); err != nil {
		return err
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].BerthID != rows[j].BerthID {
			return rows[i].BerthID < rows[j].BerthID
		}
		if rows[i].ArrivalUTC != rows[j].ArrivalUTC {
			return rows[i].ArrivalUTC < rows[j].ArrivalUTC
		}
		return rows[i].VoyageID < rows[j].VoyageID
	})
	b, err := json.Marshal(rows)
	if err != nil {
		return err
	}
	return os.WriteFile(SnapshotPath, b, 0o644)
}

func ReadSnapshot() ([]model.SnapshotRow, error) {
	b, err := os.ReadFile(SnapshotPath)
	if err != nil {
		return nil, err
	}
	var rows []model.SnapshotRow
	if err := json.Unmarshal(b, &rows); err != nil {
		return nil, err
	}
	return rows, nil
}
