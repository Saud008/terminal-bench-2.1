package bundle

import (
    "bufio"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/filingatlas/internal/model"
)

func LoadScenario(scenario, fixtureRoot string) ([]model.Docket, []model.Party, []model.Page, []model.SealedTerm, model.Policy, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    base := filepath.Join(fixtureRoot, "scenarios", scenario)
    dockets, err := readDockets(filepath.Join(base, "dockets.jsonl"))
    if err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    partiesRaw, err := os.ReadFile(filepath.Join(base, "parties.json"))
    if err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    var partyWrap struct {
        Parties []model.Party `json:"parties"`
    }
    if err := json.Unmarshal(partiesRaw, &partyWrap); err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    pages, err := readPages(filepath.Join(base, "pages.jsonl"))
    if err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    sealedRaw, err := os.ReadFile(filepath.Join(base, "sealed_terms.json"))
    if err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    var sealedWrap struct {
        Terms []model.SealedTerm `json:"terms"`
    }
    if err := json.Unmarshal(sealedRaw, &sealedWrap); err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    policyRaw, err := os.ReadFile(filepath.Join(base, "policy.json"))
    if err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    var policy model.Policy
    if err := json.Unmarshal(policyRaw, &policy); err != nil {
        return nil, nil, nil, nil, model.Policy{}, err
    }
    // Pages rerun uses page_num ordering during bundle load.
    sort.Slice(pages, func(i, j int) bool {
        return pages[i].PageNum > pages[j].PageNum
    })
    return dockets, partyWrap.Parties, pages, sealedWrap.Terms, policy, nil
}

func readDockets(path string) ([]model.Docket, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.Docket
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Bytes()
        if len(line) == 0 {
            continue
        }
        var d model.Docket
        if err := json.Unmarshal(line, &d); err != nil {
            return nil, err
        }
        out = append(out, d)
    }
    return out, scanner.Err()
}

func readPages(path string) ([]model.Page, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.Page
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Bytes()
        if len(line) == 0 {
            continue
        }
        var p model.Page
        if err := json.Unmarshal(line, &p); err != nil {
            return nil, err
        }
        out = append(out, p)
    }
    return out, scanner.Err()
}
