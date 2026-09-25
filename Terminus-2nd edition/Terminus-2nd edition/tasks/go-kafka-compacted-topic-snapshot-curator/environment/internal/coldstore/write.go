package coldstore

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/kcompactctl/internal/model"
)

const DefaultStagePath = "/app/state/frozen-segment-snapshot.json"

func WriteStage(path string, snap model.PartitionStaging) error {
    if path == "" {
        path = DefaultStagePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap.Topic, snap.Scenario, snap.Records)
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

func ReadStage(path string) (model.PartitionStaging, error) {
    if path == "" {
        path = DefaultStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.PartitionStaging{}, err
    }
    var snap model.PartitionStaging
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.PartitionStaging{}, err
    }
    return snap, nil
}

func computeDigest(topic, scenario string, records []model.StagedRecord) (string, error) {
    payload := map[string]any{
        "topic":    topic,
        "scenario": scenario,
        "records":  canonicalRecords(records),
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func canonicalRecords(records []model.StagedRecord) []map[string]any {
    out := make([]map[string]any, len(records))
    for i, rec := range records {
        out[i] = map[string]any{
            "canonical_key": rec.CanonicalKey,
            "is_tombstone":  rec.IsTombstone,
            "key_raw":       rec.KeyRaw,
            "offset":        rec.Offset,
            "partition":     rec.Partition,
            "timestamp_ms":  rec.TimestampMs,
            "value_raw":     rec.ValueRaw,
        }
    }
    return out
}
