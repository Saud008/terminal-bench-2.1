package timeline

import (
    "bufio"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/oidcgov/internal/model"
)

func LoadScenario(scenario, fixtureRoot string) ([]model.TimelineEvent, []model.TokenRecord, model.Policy, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    base := filepath.Join(fixtureRoot, "scenarios", scenario)
    timeline, err := readTimeline(filepath.Join(base, "jwks_timeline.jsonl"))
    if err != nil {
        return nil, nil, model.Policy{}, err
    }
    tokens, err := readTokens(filepath.Join(base, "token_batch.jsonl"))
    if err != nil {
        return nil, nil, model.Policy{}, err
    }
    policyRaw, err := os.ReadFile(filepath.Join(base, "policy.json"))
    if err != nil {
        return nil, nil, model.Policy{}, err
    }
    var policy model.Policy
    if err := json.Unmarshal(policyRaw, &policy); err != nil {
        return nil, nil, model.Policy{}, err
    }
    sort.Slice(timeline, func(i, j int) bool {
        return timeline[i].Epoch > timeline[j].Epoch
    })
    return timeline, tokens, policy, nil
}

func readTimeline(path string) ([]model.TimelineEvent, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.TimelineEvent
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Bytes()
        if len(line) == 0 {
            continue
        }
        var ev model.TimelineEvent
        if err := json.Unmarshal(line, &ev); err != nil {
            return nil, err
        }
        out = append(out, ev)
    }
    return out, scanner.Err()
}

func readTokens(path string) ([]model.TokenRecord, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.TokenRecord
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Bytes()
        if len(line) == 0 {
            continue
        }
        var tok model.TokenRecord
        if err := json.Unmarshal(line, &tok); err != nil {
            return nil, err
        }
        out = append(out, tok)
    }
    return out, scanner.Err()
}
