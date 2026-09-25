package pipeline

import (
    "encoding/json"
    "os"

    "github.com/terminus/wfhistctl/internal/genfold"
    "github.com/terminus/wfhistctl/internal/eventcache"
    "github.com/terminus/wfhistctl/internal/model"
)

func RunCompactPass(scenario string) error {
    snap, err := eventcache.ReadStage("")
    if err != nil {
        return err
    }
    report := genfold.Analyze(snap.Events, scenario)
    if err := writeAudit(report); err != nil {
        return err
    }
    seal := genfold.BumpSeal(model.CompactionSeal{}, report.CanBoundaries)
    return writeSeal(seal)
}

func writeAudit(report model.CompactionAudit) error {
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(report, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile("/app/work/wf-compaction-audit.json", data, 0o644)
}

func writeSeal(seal model.CompactionSeal) error {
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(seal, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile("/app/state/wf-compaction-seal.json", data, 0o644)
}

func readSeal() (model.CompactionSeal, error) {
    raw, err := os.ReadFile("/app/state/wf-compaction-seal.json")
    if err != nil {
        return model.CompactionSeal{}, err
    }
    var seal model.CompactionSeal
    if err := json.Unmarshal(raw, &seal); err != nil {
        return model.CompactionSeal{}, err
    }
    return seal, nil
}
