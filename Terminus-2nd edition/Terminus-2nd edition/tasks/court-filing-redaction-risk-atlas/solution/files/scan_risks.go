package scan

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "strings"

    "github.com/terminus/filingatlas/internal/nxtg05"
    "github.com/terminus/filingatlas/internal/nxtg02"
    "github.com/terminus/filingatlas/internal/model"
    "github.com/terminus/filingatlas/internal/nxtg01"
    "github.com/terminus/filingatlas/internal/nxtg04"
    "github.com/terminus/filingatlas/internal/nxtg03"
    "github.com/terminus/filingatlas/internal/nxtg06"
)

const findingsPath = "/app/state/risk-findings.json"

func Run(scenario string) error {
    stage, err := stagevault.ReadBundle("")
    if err != nil {
        return err
    }
    findings := Evaluate(stage, scenario)
    sort.Slice(findings, func(i, j int) bool {
        return findings[i].FindingID < findings[j].FindingID
    })
    out := model.FindingsFile{Scenario: scenario, Findings: findings}
    return writeFindings(findingsPath, out)
}

func Evaluate(stage model.BundleStage, scenario string) []model.RiskFinding {
    resolved := partygraph.ResolveAliases(stage.Parties)
    docket := docketdedup.PickPrimaryDocket(stage.Dockets)
    var out []model.RiskFinding
    seq := 0
    for _, page := range stage.Pages {
        for _, ln := range page.Lines {
            text := ln.Text
            for _, term := range stage.SealedTerms {
                if !sealedpolicy.MatchesSealed(text, term.Term) {
                    continue
                }
                seq++
                exhibits := exhibitlink.ParseExhibitRefs(text)
                exhibitRef := ""
                if len(exhibits) > 0 {
                    exhibitRef = exhibits[0]
                }
                partyID := matchParty(text, stage.Parties, resolved)
                _, lineNum := provenance.LocateLine(page, term.Term)
                out = append(out, model.RiskFinding{
                    FindingID:  fmt.Sprintf("F-%03d", seq),
                    PartyID:    partyID,
                    ExhibitRef: exhibitRef,
                    Term:       term.Term,
                    RiskLevel:  "high",
                    Page:       page.PageNum,
                    Line:       lineNum,
                    Docket:     docket,
                })
            }
        }
    }
    return out
}

func matchParty(text string, parties []model.Party, resolved map[string][]string) string {
    lower := strings.ToLower(text)
    for _, p := range parties {
        if strings.Contains(lower, strings.ToLower(p.Name)) {
            return p.ID
        }
    }
    for _, p := range parties {
        for _, alias := range resolved[p.ID] {
            if strings.Contains(lower, strings.ToLower(alias)) {
                return p.ID
            }
        }
    }
    return ""
}

func writeFindings(path string, out model.FindingsFile) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(out, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}
