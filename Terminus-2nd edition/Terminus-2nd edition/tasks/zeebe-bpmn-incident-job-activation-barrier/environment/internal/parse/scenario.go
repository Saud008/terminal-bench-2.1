package parse

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/actplay/internal/model"
)

func LoadScenario(path string) (model.Scenario, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.Scenario{}, fmt.Errorf("parse scenario: %w", err)
	}
	return sc, nil
}
