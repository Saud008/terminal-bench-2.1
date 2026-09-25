package publish

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/oidcgov/internal/model"
)

const (
    defaultOut   = "/app/output/verification-governance-report.json"
    revisionPath = "/app/state/hydrate-revision.json"
    decisionsPath = "/app/state/verification-decisions.json"
)

func Publish(scenario, outPath string) error {
    var rev model.HydrateRevision
    raw, err := os.ReadFile(revisionPath)
    if err != nil {
        return fmt.Errorf("hydrate_revision missing")
    }
    if err := json.Unmarshal(raw, &rev); err != nil {
        return err
    }
    if rev.HydrateRevision <= 0 {
        return fmt.Errorf("emit blocked: hydrate_revision must be > 0")
    }
    decRaw, err := os.ReadFile(decisionsPath)
    if err != nil {
        return err
    }
    var dec model.DecisionsFile
    if err := json.Unmarshal(decRaw, &dec); err != nil {
        return err
    }
    decisions := dec.Decisions
    sort.Slice(decisions, func(i, j int) bool {
        return decisions[i].TokenID > decisions[j].TokenID
    })
    report := model.GovernanceReport{
        Scenario:      scenario,
        DecisionCount: len(decisions),
        Decisions:     decisions,
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

func reportDigest(report model.GovernanceReport) (string, error) {
    payload := map[string]any{
        "decision_count": report.DecisionCount,
        "decisions":      report.Decisions,
        "scenario":       report.Scenario,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func writeReport(path string, report model.GovernanceReport) error {
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
