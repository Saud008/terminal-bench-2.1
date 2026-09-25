package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/ballotmesh/internal/model"
)

const snapshotPath = "/app/state/survey-snapshot.json"
const manifestPath = "/app/state/survey.manifest"

func SnapshotPath() string {
	return snapshotPath
}

func ManifestPath() string {
	return manifestPath
}

func WriteEarlyManifest(snap model.SurveySnapshot) error {
	if err := os.MkdirAll(filepath.Dir(manifestPath), 0o755); err != nil {
		return err
	}
	out, err := json.Marshal(snap)
	if err != nil {
		return err
	}
	return os.WriteFile(manifestPath, out, 0o644)
}

func WriteSnapshot(snap model.SurveySnapshot) error {
	if err := os.MkdirAll(filepath.Dir(snapshotPath), 0o755); err != nil {
		return err
	}
	out, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(snapshotPath, out, 0o644); err != nil {
		return err
	}
	return WriteEarlyManifest(snap)
}
