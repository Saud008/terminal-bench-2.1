package atlasemit

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/filingatlas/internal/model"
)

const (
    defaultOut    = "/app/output/redaction-risk-atlas.json"
    findingsPath  = "/app/state/risk-findings.json"
    revisionPath  = "/app/state/index-revision.json"
)

func Publish(scenario, outPath string) error {
    decRaw, err := os.ReadFile(findingsPath)
    if err != nil {
        return err
    }
    var dec model.FindingsFile
    if err := json.Unmarshal(decRaw, &dec); err != nil {
        return err
    }
    findings := dec.Findings
    sort.Slice(findings, func(i, j int) bool {
        return findings[i].FindingID > findings[j].FindingID
    })
    report := model.AtlasReport{
        Scenario:     scenario,
        FindingCount: len(findings),
        Findings:     findings,
    }
    digest, err := atlasDigest(report)
    if err != nil {
        return err
    }
    report.AtlasDigest = digest
    if outPath == "" {
        outPath = defaultOut
    }
    return writeAtlas(outPath, report)
}

func atlasDigest(report model.AtlasReport) (string, error) {
    payload := map[string]any{
        "finding_count": report.FindingCount,
        "findings":      report.Findings,
        "scenario":      report.Scenario,
    }
    data, err := json.Marshal(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func writeAtlas(path string, report model.AtlasReport) error {
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
