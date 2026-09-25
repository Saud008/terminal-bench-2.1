package stagevault

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/oidcgov/internal/model"
)

const DefaultTranscriptPath = "/app/state/transcript-vault.json"

func WriteTranscript(path string, stage model.TranscriptStage) error {
    if path == "" {
        path = DefaultTranscriptPath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(stage.Scenario, stage.Timeline, stage.Tokens)
    if err != nil {
        return err
    }
    stage.TranscriptDigest = digest
    data, err := json.MarshalIndent(stage, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadTranscript(path string) (model.TranscriptStage, error) {
    if path == "" {
        path = DefaultTranscriptPath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.TranscriptStage{}, err
    }
    var stage model.TranscriptStage
    if err := json.Unmarshal(raw, &stage); err != nil {
        return model.TranscriptStage{}, err
    }
    return stage, nil
}

func computeDigest(scenario string, timeline []model.TimelineEvent, tokens []model.TokenRecord) (string, error) {
    payload := map[string]any{
        "scenario": scenario,
        "timeline": timeline,
        "tokens":   tokens,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}
