package loadscenario

import (
    "encoding/json"
    "fmt"
    "io"
    "os"
    "path/filepath"

    "github.com/terminus/holdfairctl/internal/model"
)

const (
    activeDB   = "/app/state/active-library.db"
    activeMeta = "/app/state/scenario-active.json"
)

func Load(fixtureRoot, scenario string) error {
    src := filepath.Join(fixtureRoot, "scenarios", scenario, "library.db")
    if _, err := os.Stat(src); err != nil {
        return fmt.Errorf("mount-library-db: missing sqlite: %w", err)
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
