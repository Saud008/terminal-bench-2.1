package registrylock

import (
    "encoding/json"
    "fmt"
    "io"
    "os"
    "path/filepath"

    "github.com/terminus/intakectl/internal/kenneldb"
    "github.com/terminus/intakectl/internal/sheltertypes"
    "github.com/terminus/intakectl/internal/weaveloom"
)

func BindRun(fixtureRoot, scenario, runID string) error {
    srcRegistry := filepath.Join(fixtureRoot, "scenarios", scenario, "registry.sqlite")
    srcArrivals := filepath.Join(fixtureRoot, "scenarios", scenario, "arrivals.jsonl")
    if _, err := os.Stat(srcRegistry); err != nil {
        return fmt.Errorf("bind: missing registry.sqlite: %w", err)
    }
    if _, err := os.Stat(srcArrivals); err != nil {
        return fmt.Errorf("bind: missing arrivals.jsonl: %w", err)
    }
    if err := os.MkdirAll("/app/state", 0o755); err != nil {
        return err
    }
    dstRegistry := fmt.Sprintf("/app/state/registry-%s.sqlite", runID)
    if err := copyFile(srcRegistry, dstRegistry); err != nil {
        return err
    }
    db, err := kenneldb.Open(dstRegistry)
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := kenneldb.ReadMeta(db)
    if err != nil {
        return err
    }
    kennels, err := kenneldb.ReadKennels(db)
    if err != nil {
        return err
    }
    quarantine, err := kenneldb.ReadQuarantine(db)
    if err != nil {
        return err
    }
    holds, err := kenneldb.ReadHolds(db)
    if err != nil {
        return err
    }
    arrivals, err := kenneldb.LoadArrivalsJSONL(srcArrivals)
    if err != nil {
        return err
    }
    digest := RegistryDigest(meta, kennels, quarantine)
    var scores []sheltertypes.PriorityScore
    for _, rec := range arrivals {
        scores = append(scores, sheltertypes.PriorityScore{
            IntakeID:      rec.IntakeID,
            AnimalID:      rec.AnimalID,
            PriorityScore: weaveloom.ComputePriorityScore(rec, holds),
        })
    }
    artifact := sheltertypes.BindArtifact{
        RunID:           runID,
        Scenario:        scenario,
        RegistryPath:    dstRegistry,
        ArrivalsPath:    srcArrivals,
        RegistryDigest:  digest,
        KennelCount:     len(kennels),
        QuarantineCount: len(quarantine),
        PriorityScores:  scores,
    }
    body, err := json.Marshal(artifact)
    if err != nil {
        return err
    }
    outPath := fmt.Sprintf("/app/state/intake-bind-%s.json", runID)
    return os.WriteFile(outPath, body, 0o644)
}

func copyFile(src, dst string) error {
    in, err := os.Open(src)
    if err != nil {
        return err
    }
    defer in.Close()
    out, err := os.Create(dst)
    if err != nil {
        return err
    }
    defer out.Close()
    _, err = io.Copy(out, in)
    return err
}
