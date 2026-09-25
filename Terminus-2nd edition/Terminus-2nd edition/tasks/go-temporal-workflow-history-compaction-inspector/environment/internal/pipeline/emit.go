package pipeline

import (
    "fmt"

    "github.com/terminus/wfhistctl/internal/dbmirror"
    "github.com/terminus/wfhistctl/internal/eventcache"
    "github.com/terminus/wfhistctl/internal/replayledger"
)

func EmitInspection(ns, scenario, dbOut, riskOut string) error {
    seal, err := readSeal()
    if err != nil {
        return err
    }
    if !replayledger.SealAllowsExport(seal) {
        return fmt.Errorf("compaction_seal must be > 0")
    }
    snap, err := eventcache.ReadStage("")
    if err != nil {
        return err
    }
    if dbOut == "" {
        dbOut = "/app/output/inspection.db"
    }
    if riskOut == "" {
        riskOut = "/app/output/replay-risk-report.jsonl"
    }
    activities, risks := replayledger.BuildInspectionSnapshot(snap.Events)
    if err := dbmirror.WriteDB(dbOut, activities); err != nil {
        return err
    }
    return replayledger.WriteRiskReport(riskOut, risks)
}
