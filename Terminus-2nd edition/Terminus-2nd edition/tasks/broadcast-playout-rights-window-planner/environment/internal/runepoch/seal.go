package runepoch

import (
    "encoding/json"
    "os"
)

func BumpPlanPass() error {
    path := "/app/state/compile-epoch.json"
    var body map[string]int
    raw, err := os.ReadFile(path)
    if err != nil {
        body = map[string]int{"plan_pass": 0}
    } else {
        _ = json.Unmarshal(raw, &body)
    }
    if body == nil {
        body = map[string]int{"plan_pass": 0}
    }
    body["plan_pass"] = body["plan_pass"] + 1
    out, _ := json.MarshalIndent(body, "", "  ")
    return os.WriteFile(path, append(out, '\n'), 0o644)
}

func PlanPass() int {
    raw, err := os.ReadFile("/app/state/compile-epoch.json")
    if err != nil {
        return 0
    }
    var body map[string]int
    _ = json.Unmarshal(raw, &body)
    return body["plan_pass"]
}
