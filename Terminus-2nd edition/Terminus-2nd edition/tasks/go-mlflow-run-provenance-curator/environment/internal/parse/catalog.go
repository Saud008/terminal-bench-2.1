package parse

import (
	"encoding/json"
	"os"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

// LoadCatalog reads scenario JSON from disk.
func LoadCatalog(path string) (model.ScenarioFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ScenarioFile{}, err
	}
	var sc model.ScenarioFile
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.ScenarioFile{}, err
	}
	return sc, nil
}
