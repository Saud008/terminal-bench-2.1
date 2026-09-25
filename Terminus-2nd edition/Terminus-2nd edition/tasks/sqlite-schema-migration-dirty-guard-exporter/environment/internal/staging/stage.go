package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/sqlitemigrate/internal/types"
)

const DefaultStagePath = "/app/state/migrate-stage.json"

// NewEmpty returns an empty stage snapshot.
func NewEmpty() *types.StageFile {
	return &types.StageFile{}
}

// Load reads a stage file from disk.
func Load(path string) (*types.StageFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var st types.StageFile
	if err := json.Unmarshal(data, &st); err != nil {
		return nil, err
	}
	return &st, nil
}

// Save writes stage state with stable formatting for tests.
func Save(path string, st *types.StageFile) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}
