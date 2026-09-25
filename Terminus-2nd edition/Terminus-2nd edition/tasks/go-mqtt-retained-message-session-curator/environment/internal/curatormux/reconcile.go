package curatormux

import (
    "encoding/json"
    "os"

    "github.com/edgeiot/mqttsessctl/internal/model"
)

func WriteReport(report model.ReconcileReport) error {
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(report, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile("/app/work/mqtt-merge-audit.json", data, 0o644)
}

func WriteSeal(seal model.CuratorSeal) error {
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(seal, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile("/app/state/session-curator-seal.json", data, 0o644)
}

func ReadSeal() (model.CuratorSeal, error) {
    raw, err := os.ReadFile("/app/state/session-curator-seal.json")
    if err != nil {
        return model.CuratorSeal{}, err
    }
    var seal model.CuratorSeal
    if err := json.Unmarshal(raw, &seal); err != nil {
        return model.CuratorSeal{}, err
    }
    return seal, nil
}

func Analyze(events []model.JournalEvent) model.ReconcileReport {
    var findings []model.Finding
    for _, ev := range events {
        if ev.Kind == "PUBLISH" && ev.QoS > 2 {
            findings = append(findings, model.Finding{
                Code:     "QOS_RANGE",
                ClientID: ev.ClientID,
                Topic:    ev.Topic,
                Detail:   "qos out of range",
            })
        }
    }
    return model.ReconcileReport{
        Scenario:     "",
        FindingCount: len(findings),
        Findings:     findings,
    }
}

func IncrementCuratorSeal(cur model.CuratorSeal) model.CuratorSeal {
    cur.CuratorSeal = cur.CuratorSeal
    return cur
}
