package syndemit

import (
    "encoding/json"
    "os"

    "github.com/terminus/gridplan/internal/model"
)

func writeConflicts(scenario string, entries []model.PlanEntry) error {
    conflicts := make([]map[string]any, 0)
    for _, row := range entries {
        switch row.Status {
        case "rights_denied":
            conflicts = append(conflicts, map[string]any{
                "kind": "rights_violation", "detail": row.ProgramID,
            })
        case "blackout":
            conflicts = append(conflicts, map[string]any{
                "kind": "blackout_block", "detail": row.ProgramID,
            })
        }
    }
    logRaw, err := os.ReadFile("/app/work/window-compile-log.json")
    if err == nil {
        var logBody map[string]any
        if json.Unmarshal(logRaw, &logBody) == nil {
            audit, _ := logBody["marker_audit"].([]any)
            for _, item := range audit {
                m, _ := item.(map[string]any)
                if int(m["marker_count"].(float64)) == 0 {
                    conflicts = append(conflicts, map[string]any{
                        "kind": "ad_marker_dropped", "detail": m["program_id"],
                    })
                }
            }
        }
    }
    body := map[string]any{"scenario": scenario, "conflicts": conflicts}
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/output/conflict-report.json", append(raw, '\n'), 0o644)
}
