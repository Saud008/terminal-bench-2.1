package xdsbridge

import (
    "github.com/terminus/xsnapctl/internal/scenpair"
    "github.com/terminus/xsnapctl/internal/model"
    "github.com/terminus/xsnapctl/internal/sealio"
)

func MaterializePair(scenario, fixtureRoot string) (model.StagingFile, error) {
    left, right, err := scenpair.LoadPair(scenario, fixtureRoot)
    if err != nil {
        return model.StagingFile{}, err
    }
    return model.StagingFile{
        Engine:   "xsnapctl",
        Scenario: scenario,
        Left:     left,
        Right:    right,
    }, nil
}

func PersistStaging(snap model.StagingFile) error {
    return sealio.WriteStage("", snap)
}
