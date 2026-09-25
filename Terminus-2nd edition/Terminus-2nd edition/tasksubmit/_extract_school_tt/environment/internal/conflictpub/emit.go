package conflictpub

import (
    "encoding/json"
    "os"
)

func Emit(scenario string, logBody map[string]any) error {
    assignments, _ := logBody["assignments"].([]any)
    conflicts := make([]map[string]any, 0)
    seenRoom := map[string]int{}
    for _, row := range assignments {
        m, _ := row.(map[string]any)
        key := m["room_id"].(string) + "|" + m["slot_id"].(string)
        seenRoom[key] = seenRoom[key] + 1
    }
    for key, count := range seenRoom {
        if count > 1 {
            conflicts = append(conflicts, map[string]any{
                "kind": "room_double_book", "detail": key,
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
