package conflictpub

import (
    "encoding/json"
    "os"
)

func Emit(scenario string, logBody map[string]any) error {
    assignments, _ := logBody["assignments"].([]any)
    conflicts := make([]map[string]any, 0)
    teacherSlot := map[string]int{}
    roomLoad := map[string]int{}
    splitSlots := map[string]map[string]bool{}
    for _, row := range assignments {
        m, _ := row.(map[string]any)
        ts := m["teacher_id"].(string) + "|" + m["slot_id"].(string)
        teacherSlot[ts]++
        rs := m["room_id"].(string) + "|" + m["slot_id"].(string)
        roomLoad[rs]++
    }
    for key, count := range teacherSlot {
        if count > 1 {
            conflicts = append(conflicts, map[string]any{"kind": "teacher_double_book", "detail": key})
        }
    }
    for key, count := range roomLoad {
        if count > 1 {
            conflicts = append(conflicts, map[string]any{"kind": "room_double_book", "detail": key})
        }
    }
    _ = splitSlots
    body := map[string]any{"scenario": scenario, "conflicts": conflicts}
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile("/app/output/conflict-report.json", append(raw, '\n'), 0o644)
}
