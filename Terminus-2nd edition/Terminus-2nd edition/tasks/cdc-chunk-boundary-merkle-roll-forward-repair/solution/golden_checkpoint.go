package checkpoint

import (
	"encoding/base64"
	"encoding/json"
	"os"

	"github.com/terminus/cdcctl/internal/chunk"
	"github.com/terminus/cdcctl/internal/model"
)

func Load(path string) (model.Checkpoint, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Checkpoint{}, err
	}
	var cp model.Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		return model.Checkpoint{}, err
	}
	return cp, nil
}

func Save(path string, cp model.Checkpoint) error {
	data, err := json.MarshalIndent(cp, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

func RuntimeFrom(cp model.Checkpoint) chunk.Runtime {
	return chunk.NewRuntime(cp.ChunkStart, WindowFrom(cp))
}

func WindowFrom(cp model.Checkpoint) []byte {
	if cp.Window == "" {
		return nil
	}
	out, err := base64.StdEncoding.DecodeString(cp.Window)
	if err != nil {
		return nil
	}
	return out
}

func EncodeWindow(window []byte) string {
	if len(window) == 0 {
		return ""
	}
	return base64.StdEncoding.EncodeToString(window)
}
