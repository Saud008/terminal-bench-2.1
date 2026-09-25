package timetablepub

import (
    "encoding/json"
    "fmt"
    "os"

    "github.com/terminus/ttalloc/internal/allocgate"
    "github.com/terminus/ttalloc/internal/conflictpub"
)

func Publish(scenario string) error {
    if allocgate.AllocationPass() <= 0 {
        return fmt.Errorf("publish-atlas: allocation_pass is zero")
    }
    logRaw, err := os.ReadFile("/app/work/allocate-log.json")
    if err != nil {
        return err
    }
    var logBody map[string]any
    if err := json.Unmarshal(logRaw, &logBody); err != nil {
        return err
    }
    graphRaw, _ := os.ReadFile("/app/state/constraint-graph.json")
    var graph map[string]any
    _ = json.Unmarshal(graphRaw, &graph)
    atlas := map[string]any{
        "scenario": scenario,
        "engine": "ttalloc",
        "graph_fingerprint": graph["graph_fingerprint"],
        "assignments": logBody["assignments"],
    }
    if err := writeAtlas(atlas); err != nil {
        return err
    }
    return conflictpub.Emit(scenario, logBody)
}

func writeAtlas(body map[string]any) error {
    raw, err := json.MarshalIndent(body, "", "  ")
    if err != nil {
        return err
    }
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    return os.WriteFile("/app/output/timetable-atlas.json", append(raw, '\n'), 0o644)
}
