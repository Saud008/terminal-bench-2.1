package walkreport

// Publish phase for publish-displacement-atlas output artifact.

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/overbookctl/internal/model"
)

const (
    planPath    = "/app/work/overbook-plan.json"
    passPath   = "/app/state/solve-pass.json"
    atlasPath = "/app/output/displacement-atlas.json"
)

type passCounter struct {
    SolvePass int `json:"solve_pass"`
}

func PublishAtlas(scenario string) error {
    var counter passCounter
    raw, err := os.ReadFile(passPath)
    if err != nil {
        return err
    }
    if err := json.Unmarshal(raw, &counter); err != nil {
        return err
    }
    if counter.SolvePass <= 0 {
        return os.ErrInvalid
    }
    logRaw, err := os.ReadFile(planPath)
    if err != nil {
        return err
    }
    var logBody struct {
        Scenario    string                 `json:"scenario"`
        Assignments []model.RoomAssignment `json:"assignments"`
        Walks       []model.WalkEntry      `json:"walks"`
        RunStamp    string                 `json:"run_stamp"`
    }
    if err := json.Unmarshal(logRaw, &logBody); err != nil {
        return err
    }
    assignments, walks := normalizeAtlasPayload(logBody.Assignments, logBody.Walks)
    sort.Slice(walks, func(i, j int) bool {
        if walks[i].WalkCostCents != walks[j].WalkCostCents {
            return walks[i].WalkCostCents < walks[j].WalkCostCents
        }
        return walks[i].ReservationID < walks[j].ReservationID
    })
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "engine":      "overbookctl",
        "run_stamp":   logBody.RunStamp,
        "assignments": assignments,
        "walks":       walks,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(atlasPath, body, 0o644)
}
