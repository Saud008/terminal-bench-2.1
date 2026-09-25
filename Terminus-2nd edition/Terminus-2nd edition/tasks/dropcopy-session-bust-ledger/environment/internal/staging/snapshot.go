package staging

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const DefaultStagePath = "/app/state/dropcopy-stage.json"

func WriteStage(path string, v any) error {
	if path == "" {
		path = DefaultStagePath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string, dest any) error {
	if path == "" {
		path = DefaultStagePath
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, dest)
}
