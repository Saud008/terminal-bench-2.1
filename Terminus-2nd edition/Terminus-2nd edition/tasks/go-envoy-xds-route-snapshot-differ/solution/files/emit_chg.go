package chgledger

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/xsnapctl/internal/model"
)

const (
    defaultOut = "/app/output/xds-diff-report.json"
    genPath    = "/app/state/normalize-revision.json"
    leftPath   = "/app/state/normalized-left.json"
    rightPath  = "/app/state/normalized-right.json"
)

func Emit(scenario, outPath string) error {
    var gen model.RevisionFile
    raw, err := os.ReadFile(genPath)
    if err != nil {
        return fmt.Errorf("normalize_revision missing")
    }
    if err := json.Unmarshal(raw, &gen); err != nil {
        return err
    }
    if gen.NormalizeRevision <= 0 {
        return fmt.Errorf("emit blocked: normalize_revision must be > 0")
    }
    left, err := readSnapshot(leftPath)
    if err != nil {
        return err
    }
    right, err := readSnapshot(rightPath)
    if err != nil {
        return err
    }
    changes := buildChanges(left, right)
    if changes == nil {
        changes = []model.DiffChange{}
    }
    sort.Slice(changes, func(i, j int) bool {
        return changes[i].Path < changes[j].Path
    })
    report := model.DiffReport{
        Scenario:    scenario,
        ChangeCount: len(changes),
        Changes:     changes,
    }
    digest, err := reportDigest(report)
    if err != nil {
        return err
    }
    report.ReportDigest = digest
    if outPath == "" {
        outPath = defaultOut
    }
    return writeReport(outPath, report)
}

func readSnapshot(path string) (model.Snapshot, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.Snapshot{}, err
    }
    var snap model.Snapshot
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.Snapshot{}, err
    }
    return snap, nil
}

func buildChanges(left, right model.Snapshot) []model.DiffChange {
    var changes []model.DiffChange
    leftRoutes := routeMap(left)
    rightRoutes := routeMap(right)
    for cluster, rv := range rightRoutes {
        if lv, ok := leftRoutes[cluster]; !ok {
            changes = append(changes, model.DiffChange{
                Path: "/routes/" + cluster, ChangeType: "added", RightValue: rv,
            })
        } else if lv != rv {
            changes = append(changes, model.DiffChange{
                Path: "/routes/" + cluster, ChangeType: "modified", LeftValue: lv, RightValue: rv,
            })
        }
    }
    for cluster, lv := range leftRoutes {
        if _, ok := rightRoutes[cluster]; !ok {
            changes = append(changes, model.DiffChange{
                Path: "/routes/" + cluster, ChangeType: "removed", LeftValue: lv,
            })
        }
    }
    return changes
}

func routeMap(snap model.Snapshot) map[string]string {
    out := map[string]string{}
    for _, group := range snap.Routes {
        for _, rule := range group.Routes {
            out[rule.Cluster] = rule.Cluster + ":" + rule.Match.Prefix + rule.Match.Path
        }
    }
    return out
}

func reportDigest(report model.DiffReport) (string, error) {
    payload := map[string]any{
        "change_count": report.ChangeCount,
        "changes":      report.Changes,
        "scenario":     report.Scenario,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func writeReport(path string, report model.DiffReport) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(report, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}
