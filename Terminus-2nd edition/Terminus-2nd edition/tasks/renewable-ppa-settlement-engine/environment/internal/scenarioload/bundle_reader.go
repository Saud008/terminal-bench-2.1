package scenarioload

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/ppareconctl/internal/model"
)

func LoadScenario(scenario, fixtureRoot string) (*model.Scenario, error) {
	path := filepath.Join(fixtureRoot, "scenarios", scenario+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read scenario: %w", err)
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return nil, fmt.Errorf("parse scenario: %w", err)
	}
	if sc.ScenarioID == "" {
		sc.ScenarioID = scenario
	}
	return &sc, nil
}
