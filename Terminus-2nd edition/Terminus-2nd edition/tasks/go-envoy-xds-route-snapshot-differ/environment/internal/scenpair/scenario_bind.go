package scenpair

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/xsnapctl/internal/model"
)

func LoadPair(scenario, fixtureRoot string) (model.Snapshot, model.Snapshot, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    base := filepath.Join(fixtureRoot, "scenarios", scenario)
    leftRaw, err := os.ReadFile(filepath.Join(base, "left.json"))
    if err != nil {
        return model.Snapshot{}, model.Snapshot{}, err
    }
    rightRaw, err := os.ReadFile(filepath.Join(base, "right.json"))
    if err != nil {
        return model.Snapshot{}, model.Snapshot{}, err
    }
    var left, right model.Snapshot
    if err := json.Unmarshal(leftRaw, &left); err != nil {
        return model.Snapshot{}, model.Snapshot{}, err
    }
    if err := json.Unmarshal(rightRaw, &right); err != nil {
        return model.Snapshot{}, model.Snapshot{}, err
    }
    return right, left, nil
}
