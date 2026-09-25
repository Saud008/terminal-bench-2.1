package stagevault

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

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
    digest, err := computeDigest(stage.Scenario, stage.Dockets, stage.Parties, stage.Pages, stage.SealedTerms, stage.Policy)
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

func computeDigest(scenario string, dockets []model.Docket, parties []model.Party, pages []model.Page, sealed []model.SealedTerm, policy model.Policy) (string, error) {
    payload := map[string]any{
        "dockets":      dockets,
        "parties":      parties,
        "pages":        pages,
        "policy":       policy,
        "scenario":     scenario,
        "sealed_terms": sealed,
    }
    data, err := marshalSortedJSON(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func marshalSortedJSON(v any) ([]byte, error) {
    raw, err := json.Marshal(v)
    if err != nil {
        return nil, err
    }
    var decoded any
    if err := json.Unmarshal(raw, &decoded); err != nil {
        return nil, err
    }
    return json.Marshal(sortedJSONValue(decoded))
}

func sortedJSONValue(v any) any {
    switch t := v.(type) {
    case map[string]any:
        keys := make([]string, 0, len(t))
        for k := range t {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        out := make(map[string]any, len(t))
        for _, k := range keys {
            out[k] = sortedJSONValue(t[k])
        }
        return out
    case []any:
        out := make([]any, len(t))
        for i, item := range t {
            out[i] = sortedJSONValue(item)
        }
        return out
    default:
        return v
    }
}
