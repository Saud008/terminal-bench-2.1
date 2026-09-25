package fixtureread

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/demurctl/internal/model"
	"github.com/terminus/demurctl/internal/yardbundle"
	"github.com/terminus/demurctl/internal/yardkernel"
)

func LoadScenario(fixtureDir, scenario string) (model.Scenario, error) {
	path := filepath.Join(fixtureDir, "scenarios", scenario+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, fmt.Errorf("read scenario %s: %w", scenario, err)
	}
	var sc model.Scenario
	if err := json.Unmarshal(data, &sc); err != nil {
		return model.Scenario{}, err
	}
	sc.GateEvents = yardbundle.SortGateEvents(sc.GateEvents)
	if seed := os.Getenv("DEMUR_SEED"); seed != "" {
		sc = yardkernel.RemapScenario(sc, seed)
	}
	return sc, nil
}
