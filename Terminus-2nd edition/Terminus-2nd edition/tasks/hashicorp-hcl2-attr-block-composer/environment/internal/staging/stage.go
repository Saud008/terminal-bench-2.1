package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/hclmerge/internal/types"
)

const DefaultStagePath = "/app/state/hcl-stage.json"

// Load reads staging JSON from disk.
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

// Save writes staging JSON with stable fragment order.
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
