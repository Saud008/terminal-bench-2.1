package parse

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/temporal-signal-replay/internal/model"
)

func LoadScenario(path string) (model.Scenario, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.Scenario{}, fmt.Errorf("decode scenario: %w", err)
	}
	if sc.WorkflowID == "" {
		return model.Scenario{}, fmt.Errorf("workflow_id required")
	}
	return sc, nil
}
