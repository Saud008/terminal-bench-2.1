package volrep

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "time"

    "github.com/terminus/snapretctl/internal/orphscan"
    "github.com/terminus/snapretctl/internal/model"
    "github.com/terminus/snapretctl/internal/bprank"
    "github.com/terminus/snapretctl/internal/nsbkt"
    "github.com/terminus/snapretctl/internal/fltstore"
)

const (
    defaultReport   = "/app/output/volsnap-audit-report.json"
    defaultDangling = "/app/output/orphan-snapshot-ledger.jsonl"
    genPath         = "/app/state/audit-pass-counter.json"
)

func Emit(scenario, reportPath, danglingPath string) error {
    var gen model.RevisionFile
    raw, err := os.ReadFile(genPath)
    if err != nil {
        return fmt.Errorf("audit_pass_seq missing")
    }
    if err := json.Unmarshal(raw, &gen); err != nil {
        return err
    }
    if gen.AuditPassSeq <= 0 {
        return fmt.Errorf("emit blocked: audit_pass_seq must be > 0")
    }
    stage, err := fltstore.ReadFleetGraph("")
    if err != nil {
        return err
    }
    report, danglingRows := buildReport(stage)
    report.Scenario = scenario
    if reportPath == "" {
        reportPath = defaultReport
    }
    if danglingPath == "" {
        danglingPath = defaultDangling
    }
    if err := writeReport(reportPath, report); err != nil {
        return err
    }
    return writeDangling(danglingPath, danglingRows)
}

func buildReport(stage model.FleetGraphFile) (model.RetentionReport, []model.DanglingRow) {
    cluster := stage.Cluster
    nowMs := cluster.AuditClockMs
    if nowMs <= 0 {
        nowMs = time.Now().UnixMilli()
    }
    var deletable []string
    protected := 0
    for _, snap := range cluster.Snapshots {
        days := bprank.RetentionDaysForSnapshot(cluster, snap)
        if bprank.IsProtected(snap, days) {
            protected++
            continue
        }
        ageDays := (nowMs - snap.CreationClock) / (86400 * 1000)
        if int(ageDays) >= days {
            deletable = append(deletable, snap.UID)
        }
    }
    sort.Strings(deletable)
    violations := nsbkt.QuotaViolations(cluster)
    report := model.RetentionReport{
        ProtectedCount:            protected,
        DeletableSnapshotUIDs:     deletable,
        QuotaViolations:           violations,
    }
    digest, _ := reportDigest(report)
    report.ReportDigest = digest
    return report, orphscan.DanglingSnapshots(cluster)
}

func reportDigest(report model.RetentionReport) (string, error) {
    payload := map[string]any{
        "deletable_snapshot_uids": report.DeletableSnapshotUIDs,
        "protected_count":       report.ProtectedCount,
        "quota_violations":      report.QuotaViolations,
        "scenario":              report.Scenario,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func writeReport(path string, report model.RetentionReport) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(report, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(path, data, 0o644)
}

func writeDangling(path string, rows []model.DanglingRow) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    var buf []byte
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        buf = append(buf, line...)
        buf = append(buf, '\n')
    }
    return os.WriteFile(path, buf, 0o644)
}
