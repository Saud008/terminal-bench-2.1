package filingbridge

import (
    "github.com/terminus/filingatlas/internal/nxtg08"
    "github.com/terminus/filingatlas/internal/nxtg07"
    "github.com/terminus/filingatlas/internal/nxtg09"
    "github.com/terminus/filingatlas/internal/model"
    "github.com/terminus/filingatlas/internal/nxtg10"
    "github.com/terminus/filingatlas/internal/nxtg06"
)

func MaterializeBundle(scenario, fixtureRoot string) (model.BundleStage, error) {
    dockets, parties, pages, sealed, policy, err := bundle.LoadScenario(scenario, fixtureRoot)
    if err != nil {
        return model.BundleStage{}, err
    }
    return model.BundleStage{
        Engine:      "filingatlas",
        Scenario:    scenario,
        Dockets:     dockets,
        Parties:     parties,
        Pages:       pages,
        SealedTerms: sealed,
        Policy:      policy,
    }, nil
}

func PersistBundle(stage model.BundleStage) error {
    return stagevault.WriteBundle("", stage)
}

func RunIndexParties(scenario string) error {
    return index.Run(scenario)
}

func RunScanRisks(scenario string) error {
    return scan.Run(scenario)
}

func SealAtlasReport(scenario, outPath string) error {
    return atlasemit.Publish(scenario, outPath)
}
