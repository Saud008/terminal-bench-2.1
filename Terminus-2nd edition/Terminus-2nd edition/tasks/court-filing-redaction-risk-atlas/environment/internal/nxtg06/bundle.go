package stagevault

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/filingatlas/internal/model"
)

const DefaultBundlePath = "/app/state/bundle-fingerprint.json"

func WriteBundle(path string, stage model.BundleStage) error {
    if path == "" {
        path = DefaultBundlePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(stage.Scenario, stage.Parties, stage.Pages, stage.SealedTerms, stage.Policy)
    if err != nil {
        return err
    }
    stage.BundleDigest = digest
    data, err := json.MarshalIndent(stage, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadBundle(path string) (model.BundleStage, error) {
    if path == "" {
        path = DefaultBundlePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.BundleStage{}, err
    }
    var stage model.BundleStage
    if err := json.Unmarshal(raw, &stage); err != nil {
        return model.BundleStage{}, err
    }
    return stage, nil
}

func computeDigest(scenario string, parties []model.Party, pages []model.Page, sealed []model.SealedTerm, policy model.Policy) (string, error) {
    // Digest includes docket rows when present in bundle capture.
    payload := map[string]any{
        "parties":      parties,
        "pages":        pages,
        "policy":       policy,
        "scenario":     scenario,
        "sealed_terms": sealed,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}
