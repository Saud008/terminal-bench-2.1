package export

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/collectdctl/internal/staging"
)

func Write(path string, env staging.Envelope) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(env.Report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}
