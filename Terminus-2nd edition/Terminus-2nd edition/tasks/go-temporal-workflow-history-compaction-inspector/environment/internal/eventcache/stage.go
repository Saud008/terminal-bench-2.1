package eventcache

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/wfhistctl/internal/model"
)

const DefaultStagePath = "/app/state/wf-history-staging.json"

func WriteStage(path string, snap model.HistoryStaging) error {
    if path == "" {
        path = DefaultStagePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap.Namespace, snap.Scenario, snap.Events)
    if err != nil {
        return err
    }
    snap.StagingDigest = digest
    snap.MaxRunGen = maxRunGen(snap.Events)
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string) (model.HistoryStaging, error) {
    if path == "" {
        path = DefaultStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.HistoryStaging{}, err
    }
    var snap model.HistoryStaging
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.HistoryStaging{}, err
    }
    return snap, nil
}

func maxRunGen(events []model.HistoryEvent) int {
    max := 0
    for _, ev := range events {
        if ev.RunGeneration > max {
            max = ev.RunGeneration
        }
    }
    return max
}

func computeDigest(ns, scenario string, events []model.HistoryEvent) (string, error) {
    payload := map[string]any{
        "namespace": ns,
        "scenario":  scenario,
        "events":    canonicalEvents(events),
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func canonicalEvents(events []model.HistoryEvent) []map[string]any {
    out := make([]map[string]any, len(events))
    for i, ev := range events {
        out[i] = map[string]any{
            "seq":            ev.Seq,
            "event_id":       ev.EventID,
            "kind":           ev.Kind,
            "workflow_id":    ev.WorkflowID,
            "run_id":         ev.RunID,
            "run_generation": ev.RunGeneration,
            "timestamp_ms":   ev.TimestampMs,
            "activity_id":    ev.ActivityID,
            "attempt":        ev.Attempt,
            "timer_id":       ev.TimerID,
            "result_status":  ev.ResultStatus,
        }
    }
    return out
}
