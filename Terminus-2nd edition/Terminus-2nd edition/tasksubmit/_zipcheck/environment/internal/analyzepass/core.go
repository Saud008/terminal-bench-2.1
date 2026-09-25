package analyzepass

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/snapretctl/internal/orphscan"
    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/bprank"
    "github.com/terminus/snapretctl/internal/claimlnk"
    "github.com/terminus/snapretctl/internal/nsbkt"
    "github.com/terminus/snapretctl/internal/fltstore"
)

const (
    findingsPath = "/app/work/scoring-findings.json"
    genPath      = "/app/state/audit-pass-counter.json"
)

func Run(scenario string) error {
    stage, err := fltstore.ReadFleetGraph("")
    if err != nil {
        return err
    }
    findings := analyze(stage)
    out := model.AnalyzeFindings{
        Scenario: scenario, FindingCount: len(findings), Findings: findings,
    }
    if err := writeFindings(out); err != nil {
        return err
    }
    return bumpRevision()
}

func analyze(stage model.FleetGraphFile) []model.Finding {
    var findings []model.Finding
    cluster := stage.Cluster
    for _, snap := range cluster.Snapshots {
        if _, ok := claimlnk.SnapshotPVC(cluster, snap); !ok {
            findings = append(findings, model.Finding{
                Code: "pvc_missing", Snapshot: snap.UID,
                Namespace: snap.Namespace, Detail: "no_pvc_join",
            })
        }
    }
    for _, row := range orphscan.DanglingSnapshots(cluster) {
        findings = append(findings, model.Finding{
            Code: "dangling_snap", Snapshot: row.UID,
            Namespace: row.Namespace, Detail: row.SourcePVC,
        })
    }
    for _, snap := range cluster.Snapshots {
        days := bprank.RetentionDaysForSnapshot(cluster, snap)
        if bprank.IsProtected(snap, days) {
            findings = append(findings, model.Finding{
                Code: "retain_pin", Snapshot: snap.UID, Detail: "protected",
            })
        }
    }
    if len(nsbkt.QuotaViolations(cluster)) > 0 {
        findings = append(findings, model.Finding{Code: "quota_pressure", Detail: "over_cap"})
    }
    sort.Slice(findings, func(i, j int) bool {
        if findings[i].Snapshot != findings[j].Snapshot {
            return findings[i].Snapshot < findings[j].Snapshot
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
    gen.AuditPassSeq = gen.AuditPassSeq
    data, err := json.MarshalIndent(gen, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(genPath, data, 0o644)
}
