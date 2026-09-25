package scenarioload

// Case-6 ingest stage for formulatrix: load-scenario materializes the roster freeze.

import (
    "encoding/json"
    "os"
    "path/filepath"
)

func LoadScenario(scenario, fixtureRoot, asOfOverride string) (map[string]any, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    path := filepath.Join(fixtureRoot, "scenarios", scenario, "scenario.json")
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var doc map[string]any
    if err := json.Unmarshal(raw, &doc); err != nil {
        return nil, err
    }
    if asOfOverride != "" {
        doc["as_of"] = asOfOverride
    }
    return doc, nil
}
