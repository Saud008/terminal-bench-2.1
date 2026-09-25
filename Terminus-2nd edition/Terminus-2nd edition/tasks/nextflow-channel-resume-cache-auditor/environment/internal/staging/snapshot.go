package staging

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/nfresume/internal/model"
)

const DefaultStagePath = "/app/state/resume-stage.json"

func WriteStage(path string, snap model.StageSnapshot) error {
	if path == "" {
		path = DefaultStagePath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o644)
}

func ReadStage(path string, dest *model.StageSnapshot) error {
	if path == "" {
		path = DefaultStagePath
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, dest)
}
