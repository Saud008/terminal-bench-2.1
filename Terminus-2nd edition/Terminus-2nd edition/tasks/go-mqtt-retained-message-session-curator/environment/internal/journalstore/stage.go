package journalstore

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/edgeiot/mqttsessctl/internal/model"
)

const DefaultJournalStagePath = "/app/state/mqtt-journal-staging.json"

func PersistJournalStage(path string, snap model.SessionStaging) error {
    if path == "" {
        path = DefaultJournalStagePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap.Broker, snap.Scenario, snap.Events)
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

func LoadJournalStage(path string) (model.SessionStaging, error) {
    if path == "" {
        path = DefaultJournalStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.SessionStaging{}, err
    }
    var snap model.SessionStaging
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.SessionStaging{}, err
    }
    return snap, nil
}

func computeDigest(broker, scenario string, events []model.JournalEvent) (string, error) {
    payload := map[string]any{
        "broker":   broker,
        "scenario": scenario,
        "events":   canonicalEvents(events),
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func canonicalEvents(events []model.JournalEvent) []map[string]any {
    out := make([]map[string]any, len(events))
    for i, ev := range events {
        out[i] = map[string]any{
            "seq":                ev.Seq,
            "kind":               ev.Kind,
            "client_id":          ev.ClientID,
            "topic":              ev.Topic,
            "filter":             ev.Filter,
            "payload":            ev.Payload,
            "qos":                ev.QoS,
            "retain":             ev.Retain,
            "packet_id":          ev.PacketID,
            "timestamp_ms":       ev.TimestampMs,
            "clean_session":      ev.CleanSession,
            "session_expiry_ms":  ev.SessionExpiryMs,
        }
    }
    return out
}
