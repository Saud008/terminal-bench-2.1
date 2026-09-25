package atlasemit

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/filingatlas/internal/model"
)

const (
    defaultOut   = "/app/output/redaction-risk-atlas.json"
    findingsPath = "/app/state/risk-findings.json"
    revisionPath = "/app/state/index-revision.json"
)

func Publish(scenario, outPath string) error {
    var rev model.IndexRevision
    raw, err := os.ReadFile(revisionPath)
    if err != nil {
        return fmt.Errorf("index_revision missing")
    }
    if err := json.Unmarshal(raw, &rev); err != nil {
        return err
    }
    if rev.IndexRevision <= 0 {
        return fmt.Errorf("emit blocked: index_revision must be > 0")
    }
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
        return findings[i].FindingID < findings[j].FindingID
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
    data, err := marshalSortedJSON(payload)
    if err != nil {
        return "", err
    }
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:]), nil
}

func marshalSortedJSON(v any) ([]byte, error) {
    raw, err := json.Marshal(v)
    if err != nil {
        return nil, err
    }
    var decoded any
    if err := json.Unmarshal(raw, &decoded); err != nil {
        return nil, err
    }
    return json.Marshal(sortedJSONValue(decoded))
}

func sortedJSONValue(v any) any {
    switch t := v.(type) {
    case map[string]any:
        keys := make([]string, 0, len(t))
        for k := range t {
            keys = append(keys, k)
        }
        sort.Strings(keys)
        out := make(map[string]any, len(t))
        for _, k := range keys {
            out[k] = sortedJSONValue(t[k])
        }
        return out
    case []any:
        out := make([]any, len(t))
        for i, item := range t {
            out[i] = sortedJSONValue(item)
        }
        return out
    default:
        return v
    }
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
