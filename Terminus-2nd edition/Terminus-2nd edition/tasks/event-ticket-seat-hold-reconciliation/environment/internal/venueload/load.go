// Load copies a scenario SQLite bundle into the active venue workspace (bundle load).
package loadvenue

import (
    "encoding/json"
    "io"
    "os"
    "path/filepath"

    "github.com/terminus/venuetixctl/internal/model"
)

const (
    activeDB   = "/app/state/event-venue.sqlite"
    activeMeta = "/app/state/event-manifest.json"
)

func Load(fixtureRoot, scenario string) error {
    src := filepath.Join(fixtureRoot, "scenarios", scenario, "venue.db")
    if _, err := os.Stat(src); err != nil {
        return err
    }
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return err
    }
    in, err := os.Open(src)
    if err != nil {
        return err
    }
    defer in.Close()
    out, err := os.Create(activeDB)
    if err != nil {
        return err
    }
    defer out.Close()
    if _, err := io.Copy(out, in); err != nil {
        return err
    }
    metaPath := filepath.Join(fixtureRoot, "scenarios", scenario, "meta.json")
    raw, err := os.ReadFile(metaPath)
    if err != nil {
        return err
    }
    var meta model.ScenarioMeta
    if err := json.Unmarshal(raw, &meta); err != nil {
        return err
    }
    meta.Scenario = scenario
    body, err := json.Marshal(meta)
    if err != nil {
        return err
    }
    return os.WriteFile(activeMeta, body, 0o644)
}
