package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/gocron-overlap-repair/internal/model"
)

func NamespacedID(seed, raw string) string {
	return fmt.Sprintf("%s:%s", seed, raw)
}

func LoadScenario(path, seed string) (model.Scenario, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.Scenario{}, err
	}
	for i := range sc.Jobs {
		sc.Jobs[i].ID = NamespacedID(seed, sc.Jobs[i].ID)
	}
	for i := range sc.Events {
		if sc.Events[i].JobID != "" {
			sc.Events[i].JobID = NamespacedID(seed, sc.Events[i].JobID)
		}
	}
	return sc, nil
}

func ScenarioPath(baseDir, scenario string) string {
	return filepath.Join(baseDir, scenario+".json")
}
