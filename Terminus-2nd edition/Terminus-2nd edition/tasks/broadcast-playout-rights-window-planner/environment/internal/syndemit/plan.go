package syndemit

import (
    "encoding/json"
    "fmt"
    "os"

    "github.com/terminus/gridplan/internal/plannerdb"
)

func SyndicatePlan(scenario string) error {
    if !Allowed() {
        return fmt.Errorf("syndicate-plan: blocked by gate")
    }
    if _, err := os.Stat("/app/work/window-compile-log.json"); err != nil {
        return fmt.Errorf("syndicate-plan: plan not built")
    }
    entries, err := plannerdb.Load(scenario)
    if err != nil {
        return err
    }
    snapRaw, _ := os.ReadFile("/app/state/runway-snapshot.json")
    var runway map[string]any
    _ = json.Unmarshal(snapRaw, &runway)
    body := map[string]any{
        "scenario": scenario,
        "engine": "gridplan",
        "runway_digest": runway["runway_digest"],
        "entries": entries,
    }
    if err := writePlan(body); err != nil {
        return err
    }
    return writeConflicts(scenario, entries)
}

func writePlan(body map[string]any) error {
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    return os.WriteFile("/app/output/syndication-plan.json", append(raw, '\n'), 0o644)
}
