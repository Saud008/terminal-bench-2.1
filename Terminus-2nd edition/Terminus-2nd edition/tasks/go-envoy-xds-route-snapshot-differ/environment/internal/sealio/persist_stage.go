package sealio

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/xsnapctl/internal/model"
)

const DefaultStagePath = "/app/state/xds-staging.json"

func WriteStage(path string, snap model.StagingFile) error {
    if path == "" {
        path = DefaultStagePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap.Scenario, snap.Left, snap.Right)
    if err != nil {
        return err
    }
    snap.StagingDigest = digest
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string) (model.StagingFile, error) {
    if path == "" {
        path = DefaultStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.StagingFile{}, err
    }
    var snap model.StagingFile
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.StagingFile{}, err
    }
    return snap, nil
}

func computeDigest(scenario string, left, right model.Snapshot) (string, error) {
    payload := map[string]any{
        "scenario": scenario,
        "left":     left,
        "right":    right,
    }
    data, err := json.MarshalIndent(payload, "", "  ")
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}
