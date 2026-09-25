package portfoliobundle

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/grantctl/internal/model"
)

func ReadScenario(fixtureDir, scenario string) (model.Scenario, error) {
	path := filepath.Join(fixtureDir, "scenarios", scenario+".json")
	body, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(body, &sc); err != nil {
		return model.Scenario{}, err
	}
	if sc.ScenarioID == "" {
		return model.Scenario{}, fmt.Errorf("scenario_id missing")
	}
	return sc, nil
}
