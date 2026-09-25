package diffseal

import (
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/spiffectl/internal/model"
)

const (
    defaultOut = "/app/output/federation-atlas.json"
    genPath    = "/app/state/trust-seal-counter.json"
    leftPath   = "/app/state/trust-left-normalized.json"
    rightPath  = "/app/state/trust-right-normalized.json"
)

func Publish(scenario, outPath string) error {
    var gen model.RevisionFile
    raw, err := os.ReadFile(genPath)
    if err != nil {
        return fmt.Errorf("seal_counter missing")
    }
    if err := json.Unmarshal(raw, &gen); err != nil {
        return err
    }
    if gen.SealCounter <= 0 {
        return fmt.Errorf("publish blocked: seal_counter must be > 0")
    }
    left, err := readBundle(leftPath)
    if err != nil {
        return err
    }
    right, err := readBundle(rightPath)
    if err != nil {
        return err
    }
    changes := buildChanges(left, right)
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

func readBundle(path string) (model.TrustDomainBundle, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.TrustDomainBundle{}, err
    }
    var bundle model.TrustDomainBundle
    if err := json.Unmarshal(raw, &bundle); err != nil {
        return model.TrustDomainBundle{}, err
    }
    return bundle, nil
}

func buildChanges(left, right model.TrustDomainBundle) []model.DiffChange {
    changes := make([]model.DiffChange, 0)
    leftMap := svidMap(left)
    rightMap := svidMap(right)
    for id, rv := range rightMap {
        if lv, ok := leftMap[id]; !ok {
            changes = append(changes, model.DiffChange{
                Path: "/x509_svid/" + id, ChangeType: "added", RightValue: rv,
            })
        } else if lv != rv {
            changes = append(changes, model.DiffChange{
                Path: "/x509_svid/" + id, ChangeType: "modified", LeftValue: lv, RightValue: rv,
            })
        }
    }
    for id, lv := range leftMap {
        if _, ok := rightMap[id]; !ok {
            changes = append(changes, model.DiffChange{
                Path: "/x509_svid/" + id, ChangeType: "removed", LeftValue: lv,
            })
        }
    }
    if left.TrustDomain != right.TrustDomain {
        changes = append(changes, model.DiffChange{
            Path: "/trust_domain", ChangeType: "modified",
            LeftValue: left.TrustDomain, RightValue: right.TrustDomain,
        })
    }
    return changes
}

func svidMap(bundle model.TrustDomainBundle) map[string]string {
    out := map[string]string{}
    for _, s := range bundle.X509SVID {
        out[s.SPIFFEID] = s.Serial + ":" + s.SPIFFEID
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
