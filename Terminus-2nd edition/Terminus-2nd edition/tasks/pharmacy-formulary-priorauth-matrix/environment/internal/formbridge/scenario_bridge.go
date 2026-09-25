package formbridge

import (
    "encoding/json"

    "github.com/terminus/formulatrix/internal/scenarioload"
    "github.com/terminus/formulatrix/internal/model"
    "github.com/terminus/formulatrix/internal/rosterfreeze"
)

func MaterializeScenario(scenario, fixtureRoot, asOf string) (model.RosterFile, error) {
    raw, err := scenarioload.LoadScenario(scenario, fixtureRoot, asOf)
    if err != nil {
        return model.RosterFile{}, err
    }
    data, err := json.Marshal(raw)
    if err != nil {
        return model.RosterFile{}, err
    }
    var scen model.ScenarioJSON
    if err := json.Unmarshal(data, &scen); err != nil {
        return model.RosterFile{}, err
    }
    return model.RosterFile{
        Engine:     "formulatrix",
        Scenario:   scenario,
        AsOf:       scen.AsOf,
        Drugs:      scen.Drugs,
        Plans:      scen.Plans,
        Overrides:  scen.Overrides,
        StepChains: scen.StepChains,
    }, nil
}

func PersistRoster(snap model.RosterFile) error {
    return rosterfreeze.WriteRoster("", snap)
}
