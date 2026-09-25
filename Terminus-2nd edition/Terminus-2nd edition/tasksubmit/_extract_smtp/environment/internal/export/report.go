package export

import (
	"encoding/json"
	"os"
	"path/filepath"

	"mailindex/internal/model"
)

func WriteReport(path string, report model.Report) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
