package syndemit

import (
    "encoding/json"
    "os"

    "github.com/terminus/gridplan/internal/model"
)

func writeConflicts(scenario string, entries []model.PlanEntry) error {
    conflicts := make([]map[string]any, 0)
    for _, row := range entries {
        if row.Status == "rights_denied" {
            conflicts = append(conflicts, map[string]any{
                "kind": "rights_violation", "detail": row.ProgramID,
            })
        }
    }
    body := map[string]any{"scenario": scenario, "conflicts": conflicts}
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/output/conflict-report.json", append(raw, '\n'), 0o644)
}
