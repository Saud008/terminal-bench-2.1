package validate

import (
	"encoding/json"
	"os"
)

// ExportAudit is a secondary report path used by diagnostics only (decoy stage).
func ExportAudit(path string, payload map[string]any) error {
	data, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}
