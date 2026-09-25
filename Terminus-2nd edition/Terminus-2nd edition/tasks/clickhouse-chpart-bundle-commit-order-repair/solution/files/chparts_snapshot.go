package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/clickparts/chparts/internal/model"
)

const snapshotPath = "/app/state/parts-snapshot.json"
const manifestPath = "/app/state/parts.manifest"

func WriteSnapshot(snap model.Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(snapshotPath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(snapshotPath, raw, 0o644)
}

func WriteEarlyManifest(snap model.Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(manifestPath), 0o755); err != nil {
		return err
	}
	early := model.Snapshot{
		TableSuffix: snap.TableSuffix,
		TableName:   snap.TableName,
		MaxBlock:    0,
		Fsynced:     false,
		Rows:        nil,
	}
	raw, err := json.MarshalIndent(early, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(manifestPath, raw, 0o644)
}

func SnapshotPath() string { return snapshotPath }
func ManifestPath() string { return manifestPath }
