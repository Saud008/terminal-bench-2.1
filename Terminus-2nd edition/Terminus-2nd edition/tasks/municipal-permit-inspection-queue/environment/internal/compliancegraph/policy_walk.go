package compliancegraph

import (
	"encoding/json"
	"os"
)

func RecordWalk(nodes []map[string]string) error {
	if err := os.MkdirAll("/app/intermediate", 0o755); err != nil {
		return err
	}
	body := map[string]any{"walk": nodes, "version": 2}
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	return os.WriteFile("/app/intermediate/compliance-trace.json", append(raw, '\n'), 0o644)
}
