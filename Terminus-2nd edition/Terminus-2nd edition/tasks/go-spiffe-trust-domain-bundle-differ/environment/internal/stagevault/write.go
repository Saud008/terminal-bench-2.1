package stagevault

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/spiffectl/internal/model"
)

const DefaultStagePath = "/app/state/pair-capture.json"

func WriteCapture(path string, snap model.PairCapture) error {
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
    snap.CaptureDigest = digest
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadCapture(path string) (model.PairCapture, error) {
    if path == "" {
        path = DefaultStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.PairCapture{}, err
    }
    var snap model.PairCapture
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.PairCapture{}, err
    }
    return snap, nil
}

func computeDigest(scenario string, left, right model.TrustDomainBundle) (string, error) {
    payload := map[string]any{
        "left":     left,
        "right":    right,
        "scenario": scenario,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}
