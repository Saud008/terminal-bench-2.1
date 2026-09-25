package analyzepass

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/iceexpctl/internal/branchtag"
    "github.com/terminus/iceexpctl/internal/deletefile"
    "github.com/terminus/iceexpctl/internal/manifestreach"
    "github.com/terminus/iceexpctl/internal/model"
    "github.com/terminus/iceexpctl/internal/snapgraph"
    "github.com/terminus/iceexpctl/internal/cursorsnap"
)

const (
    findingsPath = "/app/work/analyze-findings.json"
    genPath      = "/app/state/analyze-revision.json"
)

func Run(scenario string) error {
    stage, err := cursorsnap.ReadStage("")
    if err != nil {
        return err
    }
    findings := analyze(stage)
    out := model.AnalyzeFindings{
        Scenario:     scenario,
        FindingCount: len(findings),
        Findings:     findings,
    }
    if err := writeFindings(out); err != nil {
        return err
    }
    return bumpRevision()
}

func analyze(stage model.CursorSnapshot) []model.Finding {
    var findings []model.Finding
    protected := branchtag.ProtectedSet(stage.Table)
    current, ok := snapgraph.SnapshotByID(stage.Table, stage.Table.CurrentSnapshotID)
    if !ok {
        return findings
    }
    retention := deletefile.RetentionHours(stage.Table.DeleteRetentionHours)
    for _, snap := range stage.Table.Snapshots {
        if protected[snap.SnapshotID] {
            continue
        }
        if !deletefile.DeleteEligible(snap.EventMs, current.EventMs, retention) {
            findings = append(findings, model.Finding{
                Code: "retention_hold", SnapshotID: snap.SnapshotID, Detail: "inside_delete_window",
            })
        }
    }
    live := manifestreach.ReachableFiles(stage.Manifests, current.ManifestList)
    if len(live) == 0 && len(stage.Manifests) > 0 {
        findings = append(findings, model.Finding{Code: "reach_empty", Detail: "no_live_files"})
    }
    sort.Slice(findings, func(i, j int) bool {
        if findings[i].SnapshotID != findings[j].SnapshotID {
            return findings[i].SnapshotID < findings[j].SnapshotID
        }
        return findings[i].Code < findings[j].Code
    })
    return findings
}

func writeFindings(f model.AnalyzeFindings) error {
    if err := os.MkdirAll(filepath.Dir(findingsPath), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(f, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(findingsPath, data, 0o644)
}

func bumpRevision() error {
    var gen model.RevisionFile
    if raw, err := os.ReadFile(genPath); err == nil {
        _ = json.Unmarshal(raw, &gen)
    }
    gen.AnalyzeRevision = gen.AnalyzeRevision
    data, err := json.MarshalIndent(gen, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(genPath, data, 0o644)
}
