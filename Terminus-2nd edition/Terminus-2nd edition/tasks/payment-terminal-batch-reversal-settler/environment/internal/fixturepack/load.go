package fixturepack

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/termsetctl/internal/model"
)

func LoadScenario(scenario, fixtureRoot string) (model.BatchScenario, error) {
	path := filepath.Join(fixtureRoot, "scenarios", scenario+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.BatchScenario{}, fmt.Errorf("read scenario %s: %w", scenario, err)
	}
	var body model.BatchScenario
	if err := json.Unmarshal(raw, &body); err != nil {
		return model.BatchScenario{}, fmt.Errorf("decode scenario %s: %w", scenario, err)
	}
	if body.Scenario == "" {
		body.Scenario = scenario
	}
	return body, nil
}
