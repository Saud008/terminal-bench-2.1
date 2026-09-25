package yardsummary

import (
	"encoding/json"
	"os"

	"github.com/terminus/demurctl/internal/model"
)

// WriteDecoySummary emits informational yard summary JSON (decoy — not on publish hot path).
func WriteDecoySummary(sc model.Scenario, path string) error {
	body, err := json.Marshal(map[string]any{
		"scenario":         sc.ScenarioID,
		"container_count":  len(sc.Containers),
		"hold_count":       len(sc.Holds),
		"closure_count":    len(sc.Closures),
		"decoy_engine":     "yardsummary",
		"influences_clock": false,
	})
	if err != nil {
		return err
	}
	return os.WriteFile(path, body, 0o644)
}
