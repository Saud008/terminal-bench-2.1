package rosterfreeze

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/formulatrix/internal/model"
)

const DefaultRosterPath = "/app/state/formulary-roster.json"

func WriteRoster(path string, snap model.RosterFile) error {
    if path == "" {
        path = DefaultRosterPath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap)
    if err != nil {
        return err
    }
    snap.RosterDigest = digest
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadRoster(path string) (model.RosterFile, error) {
    if path == "" {
        path = DefaultRosterPath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.RosterFile{}, err
    }
    var snap model.RosterFile
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.RosterFile{}, err
    }
    return snap, nil
}

func computeDigest(snap model.RosterFile) (string, error) {
    payload := map[string]any{
        "as_of":       snap.AsOf,
        "drugs":       snap.Drugs,
        "overrides":   snap.Overrides,
        "plans":       snap.Plans,
        "scenario":    snap.Scenario,
        "step_chains": snap.StepChains,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}
