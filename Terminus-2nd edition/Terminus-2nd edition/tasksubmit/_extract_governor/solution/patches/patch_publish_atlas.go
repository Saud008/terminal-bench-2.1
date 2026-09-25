package atlasledger

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/holdfairctl/internal/model"
)

const (
    logPath  = "/app/work/reconcile-log.json"
    passPath = "/app/state/reconcile-pass.json"
    atlasPath = "/app/output/hold-assignment-atlas.json"
)

type passCounter struct {
    ReconcilePass int `json:"reconcile_pass"`
}

func WriteAtlas(scenario string) error {
    var counter passCounter
    raw, err := os.ReadFile(passPath)
    if err != nil {
        return err
    }
    if err := json.Unmarshal(raw, &counter); err != nil {
        return err
    }
    if counter.ReconcilePass <= 0 {
        return os.ErrInvalid
    }
    logRaw, err := os.ReadFile(logPath)
    if err != nil {
        return err
    }
    var logBody struct {
        Scenario    string              `json:"scenario"`
        Assignments []model.Assignment  `json:"assignments"`
        RunStamp    string              `json:"run_stamp"`
    }
    if err := json.Unmarshal(logRaw, &logBody); err != nil {
        return err
    }
    assignments := logBody.Assignments
    sort.SliceStable(assignments, func(i, j int) bool {
        if assignments[i].QueuePos != assignments[j].QueuePos {
            return assignments[i].QueuePos < assignments[j].QueuePos
        }
        return assignments[i].PatronID < assignments[j].PatronID
    })
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "engine":      "holdfairctl",
        "run_stamp":   logBody.RunStamp,
        "assignments": assignments,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(atlasPath, body, 0o644)
}
