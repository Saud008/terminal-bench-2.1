package spiffebridge

import (
    "github.com/terminus/spiffectl/internal/bundlescene"
    "github.com/terminus/spiffectl/internal/model"
    "github.com/terminus/spiffectl/internal/stagevault"
)

func BindPairBundles(scenario, fixtureRoot string) (model.PairCapture, error) {
    left, right, err := bundlescene.LoadPair(scenario, fixtureRoot)
    if err != nil {
        return model.PairCapture{}, err
    }
    return model.PairCapture{
        Engine:   "spiffectl",
        Scenario: scenario,
        Left:     left,
        Right:    right,
    }, nil
}

func PersistCapture(stage model.PairCapture) error {
    return stagevault.WriteCapture("", stage)
}
