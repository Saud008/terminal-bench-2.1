package fixturepack

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type Scenario struct {
	Scenario  string           `json:"scenario"`
	Bonds     []json.RawMessage `json:"bonds"`
	Trades    []json.RawMessage `json:"trades"`
	Calendars []json.RawMessage `json:"calendars"`
}

func Load(name, fixtureDir string) (Scenario, error) {
	path := filepath.Join(fixtureDir, "scenarios", name+".json")
	raw, err := os.ReadFile(path)
	if err != nil {
		return Scenario{}, err
	}
	var sc Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return Scenario{}, err
	}
	if sc.Scenario == "" {
		sc.Scenario = name
	}
	return sc, nil
}

func FixtureDir() string {
	if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
		return v
	}
	return "/app/fixtures"
}

func ExDaysOverride(def int) int {
	if v := os.Getenv("TB3_EX_DAYS"); v != "" {
		var n int
		fmt.Sscanf(v, "%d", &n)
		if n > 0 {
			return n
		}
	}
	return def
}
