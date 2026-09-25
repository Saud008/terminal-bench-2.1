package bundlescene

import (
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/spiffectl/internal/model"
)

func LoadPair(scenario, fixtureRoot string) (model.TrustDomainBundle, model.TrustDomainBundle, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    base := filepath.Join(fixtureRoot, "scenarios", scenario)
    leftRaw, err := os.ReadFile(filepath.Join(base, "left.json"))
    if err != nil {
        return model.TrustDomainBundle{}, model.TrustDomainBundle{}, err
    }
    rightRaw, err := os.ReadFile(filepath.Join(base, "right.json"))
    if err != nil {
        return model.TrustDomainBundle{}, model.TrustDomainBundle{}, err
    }
    var left, right model.TrustDomainBundle
    if err := json.Unmarshal(leftRaw, &left); err != nil {
        return model.TrustDomainBundle{}, model.TrustDomainBundle{}, err
    }
    if err := json.Unmarshal(rightRaw, &right); err != nil {
        return model.TrustDomainBundle{}, model.TrustDomainBundle{}, err
    }
    return left, right, nil
}
