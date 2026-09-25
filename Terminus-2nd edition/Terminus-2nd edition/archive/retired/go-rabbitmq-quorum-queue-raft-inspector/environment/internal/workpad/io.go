package workpad

import (
    "encoding/json"
    "os"

    "github.com/terminus/qqraftctl/internal/model"
)

const DefaultPath = "/app/state/raft-staging.json"

func Write(path string, st model.Staging) error {
    raw, err := json.MarshalIndent(st, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(path, append(raw, '\n'), 0o644)
}

func Read(path string) (model.Staging, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.Staging{}, err
    }
    var st model.Staging
    if err := json.Unmarshal(raw, &st); err != nil {
        return model.Staging{}, err
    }
    return st, nil
}
