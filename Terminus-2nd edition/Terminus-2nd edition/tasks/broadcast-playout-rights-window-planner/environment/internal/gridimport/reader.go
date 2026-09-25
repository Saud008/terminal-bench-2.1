package gridimport

// Schedule bundle import copies fixture JSON into active-grid state.

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
)

func Load(fixtureRoot, scenario string) error {
    src := filepath.Join(fixtureRoot, "scenarios", scenario)
    bundlePath := filepath.Join(src, "bundle.json")
    raw, err := os.ReadFile(bundlePath)
    if err != nil {
        return fmt.Errorf("import-grid: read bundle: %w", err)
    }
    var body map[string]any
    if err := json.Unmarshal(raw, &body); err != nil {
        return err
    }
    body["scenario"] = scenario
    out, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return err
    }
    if err := os.WriteFile("/app/state/active-grid.json", append(out, '\n'), 0o644); err != nil {
        return err
    }
    meta := map[string]any{"scenario": scenario, "seed": body["seed"]}
    mb, _ := json.MarshalIndent(meta, "", "  ")
    return os.WriteFile("/app/state/scenario-active.json", append(mb, '\n'), 0o644)
}
