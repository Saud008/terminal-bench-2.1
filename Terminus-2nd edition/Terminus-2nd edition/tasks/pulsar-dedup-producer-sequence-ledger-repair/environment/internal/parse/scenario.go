package parse

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/pulsar-dedup-replay/internal/model"
)

func LoadScenario(path string) (model.Scenario, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.Scenario{}, fmt.Errorf("invalid scenario json: %w", err)
	}
	if sc.Tenant == "" {
		return model.Scenario{}, fmt.Errorf("tenant required")
	}
	if sc.DedupWindow <= 0 {
		return model.Scenario{}, fmt.Errorf("dedup_window must be positive")
	}
	if len(sc.Events) == 0 {
		return model.Scenario{}, fmt.Errorf("events required")
	}
	return sc, nil
}
