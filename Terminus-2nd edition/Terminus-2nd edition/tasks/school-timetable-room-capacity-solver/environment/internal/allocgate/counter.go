package allocgate

import (
    "encoding/json"
    "os"
)

func BumpAllocationPass() error {
    path := "/app/state/allocation-pass.json"
    var body map[string]int
    raw, err := os.ReadFile(path)
    if err != nil {
        body = map[string]int{"allocation_pass": 0}
    } else {
        _ = json.Unmarshal(raw, &body)
    }
    if body == nil {
        body = map[string]int{"allocation_pass": 0}
    }
    body["allocation_pass"] = body["allocation_pass"] + 1
    out, _ := json.MarshalIndent(body, "", "  ")
    return os.WriteFile(path, append(out, '\n'), 0o644)
}

func AllocationPass() int {
    raw, err := os.ReadFile("/app/state/allocation-pass.json")
    if err != nil {
        return 0
    }
    var body map[string]int
    _ = json.Unmarshal(raw, &body)
    return body["allocation_pass"]
}
